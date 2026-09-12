"""Build an immutable Go byte dataset from existing external Gold JSONL corpora."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from typing import Any

from encoding import COLUMNS, Schema, digest, encode, little_endian_bytes, padded_window, repair_missing_tildes, windows
from repair import SyntaxRepairer
from splitting import assign_groups, natural_balance

REPOSITORY = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY / "training/go/corpora.json"
TOOLCHAIN = "go1.27.1"
FORMAT = "nsh-go-byte-dataset-v1"
SPLITS = ("train", "validation", "test")


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_hash(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            checksum.update(block)
    return checksum.hexdigest()


def dataset_root() -> Path:
    return Path(os.environ.get("NSH_DATASET_ROOT", Path.home() / "Datasets/neural-semantic-highlighting")) / "go"


class Groups:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, item: str) -> str:
        self.parent.setdefault(item, item)
        root = item
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[item] != item:
            parent = self.parent[item]
            self.parent[item] = root
            item = parent
        return root

    def union(self, left: str, right: str) -> None:
        a, b = sorted((self.find(left), self.find(right)))
        self.parent[b] = a


def source_group(spec: dict, manifest: dict, record: dict) -> str:
    if spec["kind"] == "focused":
        return "family:" + record["family"]
    if spec["kind"] == "module":
        # Versions/platform variants of the same module stay in one split.
        return "module:" + manifest["source"]["module"]
    package = record["package"].split("/")
    # Keep net/... together, internal/runtime/... together, etc.
    prefix = "/".join(package[:2] if package[0] == "internal" else package[:1])
    return "stdlib:" + prefix


def hash_split(group: str, seed: int) -> str:
    bucket = int(digest(f"{seed}:{group}".encode())[:16], 16) / 2**64
    return "train" if bucket < 0.8 else "validation" if bucket < 0.9 else "test"


def focused_copy_exclusions(provenance: dict[str, list[dict]], hints: dict[str, set[str]], copies: Groups) -> tuple[list[dict], set[str]]:
    """Drop train-only mined examples that are near-copies of held-out focused data.

    Synthetic train/validation/test families still fail closed. The miner is an
    opportunistic source of extra training examples, so losing a colliding mined
    example is preferable to weakening a held-out split.
    """
    targeted_generator = "targeted-go-feature-miner-v1"
    members: dict[str, set[str]] = defaultdict(set)
    component_hints: dict[str, set[str]] = defaultdict(set)
    for sha, origins in provenance.items():
        component = copies.find(sha)
        members[component].add(sha)
        for origin in origins:
            component_hints[component].update(hints.get(origin["group"], set()))

    excluded_origins: list[dict] = []
    excluded_documents: set[str] = set()
    for component, values in component_hints.items():
        if len(values) <= 1:
            continue
        active_hints: set[str] = set()
        targeted_origins: list[dict] = []
        removable: set[str] = set()
        active_groups: set[str] = set()
        for sha in members[component]:
            origins = provenance[sha]
            active = []
            for origin in origins:
                if origin.get("focusedGenerator") == targeted_generator and origin.get("split") == "train":
                    targeted_origins.append({"documentId": sha, **origin})
                else:
                    active.append(origin)
                    active_groups.add(origin["group"])
                    active_hints.update(hints.get(origin["group"], set()))
            if origins and not active:
                removable.add(sha)
        if len(active_hints) > 1:
            raise ValueError(
                f"Near-copy/template split conflict in {component}: {sorted(active_hints)}; "
                f"families={sorted(active_groups)}; revise templates instead of leaking them"
            )
        if targeted_origins and active_hints:
            excluded_origins.extend(
                {"copyFamily": component, "reason": "targeted-train-near-heldout-focused-copy", **origin}
                for origin in targeted_origins
            )
            excluded_documents.update(removable)
    return excluded_origins, excluded_documents


def build(root: Path, config_path: Path, output: Path, *, max_length: int = 512, seed: int = 1729) -> dict:
    if max_length != 512:
        raise ValueError("This baseline is fixed at 512 UTF-8 bytes; do not change context silently")
    schema_path = REPOSITORY / "packs/go/schema.json"
    schema = Schema.load(schema_path)
    config = load(config_path)
    if config.get("formatVersion") != 1:
        raise ValueError("Unsupported corpus selection format")
    specs = config["sources"]
    if len({spec["id"] for spec in specs}) != len(specs):
        raise ValueError("Duplicate source ids in corpus selection")
    sealed = [spec["id"] for spec in specs if str(spec.get("id", "")).startswith("sealed-")]
    if sealed:
        raise ValueError(
            "Sealed acceptance corpora can never enter a prepared training snapshot: " + ", ".join(sorted(sealed))
        )
    inputs = []
    resolved_root = root.resolve()
    for spec in specs:
        folder = (root / spec["directory"]).resolve()
        if not folder.is_relative_to(resolved_root):
            raise ValueError("A corpus directory escapes the dataset root")
        if spec["kind"] not in {"stdlib", "module", "focused"}:
            raise ValueError("Unknown corpus kind")
        manifest_path, gold_path = folder / "sample.json", folder / "labeled-sample.jsonl"
        if not manifest_path.is_file() or not gold_path.is_file():
            raise ValueError(f"Missing corpus {spec['id']}: run its collection command first ({folder})")
        if (folder / ".dataset.lock").exists():
            raise ValueError(f"Corpus is currently being written: {spec['id']}")
        manifest = load(manifest_path)
        if manifest.get("toolchain") != TOOLCHAIN or manifest.get("corpus") != spec["id"]:
            raise ValueError(f"Wrong toolchain or corpus identity: {spec['id']}")
        if spec["kind"] == "module" and manifest.get("source", {}).get("module") != spec["module"]:
            raise ValueError(f"Module identity mismatch: {spec['id']}")
        if spec["kind"] == "focused" and manifest.get("kind") != "focused":
            raise ValueError("Expected focused corpus metadata")
        inputs.append((spec, manifest, gold_path, manifest_path))
    # Hash before building; the same input snapshot is immutable and replayable.
    identity = {
        "format": FORMAT, "schema": file_hash(schema_path), "contextBytes": max_length, "seed": seed,
        "config": config, "builder": {p.name: file_hash(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
        "syntaxRepair": {"toolchain": TOOLCHAIN,
                         "sources": {str(p.relative_to(REPOSITORY)): file_hash(p)
                                     for p in sorted((REPOSITORY / "packs/go/labeling").rglob("*.go"))
                                     if not p.name.endswith("_test.go")},
                         "module": file_hash(REPOSITORY / "packs/go/go.mod")},
        "inputs": [{"corpus": s["id"], "manifestHash": file_hash(m), "goldHash": file_hash(p)} for s, _, p, m in inputs],
    }
    snapshot = digest(dumps(identity).encode())
    destination = output / snapshot[:20]
    output.mkdir(parents=True, exist_ok=True)
    lock = output / ".prepare.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError(f"Another preparation may be active: {lock}") from error
    os.close(fd)
    try:
        if destination.exists():
            report = load(destination / "manifest.json")
            if report.get("snapshot") != snapshot:
                raise ValueError("Existing dataset snapshot has a different identity")
            verify_output(destination, report)
            publish_pointer(output, destination)
            print(f"Reusing verified snapshot: {destination}", flush=True)
            return report
        with tempfile.TemporaryDirectory(prefix=".prepare-", dir=output) as temporary:
            stage = Path(temporary)
            report = build_stage(stage, inputs, schema, identity, snapshot, max_length, seed)
            # Ensure none of the input corpora changed during the build.
            for (_, _, path, manifest), expected in zip(inputs, identity["inputs"]):
                if file_hash(path) != expected["goldHash"] or file_hash(manifest) != expected["manifestHash"]:
                    raise ValueError("Input corpus changed while preparing; no snapshot was published")
            (stage / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            stage.rename(destination)
        publish_pointer(output, destination)
        return report
    finally:
        lock.unlink(missing_ok=True)


def publish_pointer(output: Path, destination: Path) -> None:
    temporary = output / ".current.json.tmp"
    temporary.write_text(dumps({"snapshotDirectory": destination.name}) + "\n", encoding="utf-8")
    temporary.replace(output / "current.json")


def verify_output(directory: Path, report: dict) -> None:
    for relative, expected in report["checksums"].items():
        path = directory / relative
        if not path.is_file() or file_hash(path) != expected:
            raise ValueError(f"Corrupted prepared dataset file: {path}")


def build_stage(stage: Path, inputs: list, schema: Schema, identity: dict, snapshot: str, size: int, seed: int) -> dict:
    database = stage / "index.sqlite3"
    db = sqlite3.connect(database)
    copies = Groups()
    features: dict[str, set[str]] = defaultdict(set)
    hints: dict[str, set[str]] = defaultdict(set)
    shapes: dict[str, str] = {}
    normalized: dict[str, str] = {}
    provenance: dict[str, list[dict]] = defaultdict(list)
    counts = Counter()
    by_corpus = {}
    try:
        db.execute("CREATE TABLE documents (hash TEXT PRIMARY KEY, group_id TEXT, raw TEXT, gold_hash TEXT, stream TEXT, weight INTEGER)")
        with SyntaxRepairer(REPOSITORY, TOOLCHAIN) as repairer, (stage / "quarantine.jsonl").open("w", encoding="utf-8") as quarantine:
            for spec, manifest, path, _ in inputs:
                print(f"Indexing {spec['id']} ...", flush=True)
                selected = {(x["package"], x["path"]): x for x in manifest["files"]}
                if len(selected) != len(manifest["files"]):
                    raise ValueError(f"Duplicate manifest file: {spec['id']}")
                seen = set()
                corpus_counts = Counter()
                with path.open(encoding="utf-8") as stream:
                    for line_number, line in enumerate(stream, 1):
                        if not line.strip():
                            raise ValueError(f"Blank JSONL record: {spec['id']}:{line_number}")
                        record = json.loads(line)
                        key = (record["package"], record["path"])
                        expected = selected.get(key)
                        if key in seen or expected is None:
                            raise ValueError(f"Duplicate or unexpected document: {spec['id']}:{key}")
                        seen.add(key)
                        source_bytes = record["source"].encode("utf-8")
                        if expected["contentHash"] != record["contentHash"] or expected["size"] != len(source_bytes):
                            raise ValueError(f"Manifest differs from Gold document: {spec['id']}:{key}")
                        corpus_counts["inputDocuments"] += 1
                        counts["inputDocuments"] += 1
                        record, repaired = repair_missing_tildes(record)
                        counts["repairedTildeOperators"] += repaired
                        corpus_counts["repairedTildeOperators"] += repaired
                        try:
                            try:
                                encoded = encode(record, schema)
                            except ValueError as error:
                                if "Unlabeled non-whitespace" not in str(error):
                                    raise
                                # Repair only a known, AST-confirmed declaration omission.
                                # All remaining holes still fail the same completeness check.
                                record, repaired_guards = repairer.repair(record)
                                counts["repairedTypeSwitchDeclarations"] += repaired_guards
                                corpus_counts["repairedTypeSwitchDeclarations"] += repaired_guards
                                encoded = encode(record, schema)
                                if repaired_guards:
                                    counts["recoveredTypeSwitchDocuments"] += 1
                                    corpus_counts["recoveredTypeSwitchDocuments"] += 1
                        except ValueError as error:
                            if "Unlabeled non-whitespace" not in str(error):
                                raise ValueError(f"{spec['id']}:{key}: {error}") from error
                            quarantine.write(dumps({"corpus": spec["id"], "package": key[0], "path": key[1], "reason": str(error)}) + "\n")
                            counts["quarantinedDocuments"] += 1
                            corpus_counts["quarantinedDocuments"] += 1
                            continue
                        group = source_group(spec, manifest, record)
                        if spec["kind"] == "focused":
                            hint = record.get("split")
                            if hint not in SPLITS:
                                raise ValueError("Focused records require an explicit family split")
                            hints[group].add(hint)
                            features[record["contentHash"]].update(record["features"])
                        sha = record["contentHash"]
                        origin = {"corpus": spec["id"], "package": key[0], "path": key[1], "group": group,
                                  "source": manifest.get("source"), "toolchain": manifest["toolchain"],
                                  "build": [manifest.get("goos"), manifest.get("goarch")],
                                  "goldMode": "legacy-stdlib" if spec["kind"] == "stdlib" else "strict"}
                        if spec["kind"] == "focused":
                            origin.update(family=record["family"], since=record["since"], variant=record["variant"],
                                          split=record["split"], focusedGenerator=manifest.get("generator"))
                        provenance[sha].append(origin)
                        gold_hash = digest(dumps(record["result"]).encode())
                        old = db.execute("SELECT group_id, gold_hash FROM documents WHERE hash=?", (sha,)).fetchone()
                        if old:
                            if old[1] != gold_hash:
                                raise ValueError(f"Identical source has conflicting Gold labels: {spec['id']}:{key}; resolve before training")
                            counts["exactDuplicatesRemoved"] += 1
                        else:
                            weight = len(windows(encoded, size, False)[0])
                            db.execute("INSERT INTO documents VALUES (?,?,?,?,?,?)", (sha, group, dumps(record), gold_hash,
                                       "focus" if spec["kind"] == "focused" else "natural", weight))
                        # Link document hashes, not entire modules. Shared boilerplate must
                        # not transitively fuse unrelated source groups into a giant group.
                        copies.find(sha)
                        for inventory, fingerprint in ((normalized, encoded.normalized_hash), (shapes, encoded.shape_hash)):
                            if fingerprint in inventory:
                                copies.union(sha, inventory[fingerprint])
                            else:
                                inventory[fingerprint] = sha
                        corpus_counts["acceptedDocuments"] += 1
                        if line_number % 200 == 0:
                            print(f"  {spec['id']}: {line_number}/{len(selected)} documents", flush=True)
                if seen != set(selected):
                    raise ValueError(f"Incomplete JSONL corpus: {spec['id']}")
                by_corpus[spec["id"]] = dict(corpus_counts)
                db.commit()
        # Exclude cross-source natural clone families instead of assigning all
        # their parent modules to one split. Within-source copies remain together.
        # Focused structural families retain their explicitly held-out splits.
        copy_origins: dict[str, set[str]] = defaultdict(set)
        copy_hints: dict[str, set[str]] = defaultdict(set)
        copy_members: dict[str, set[str]] = defaultdict(set)
        for sha, origins in provenance.items():
            component = copies.find(sha)
            copy_members[component].add(sha)
            for origin in origins:
                copy_origins[component].add(origin["group"])
                copy_hints[component].update(hints.get(origin["group"], set()))

        targeted_excluded_origins, targeted_excluded_documents = focused_copy_exclusions(provenance, hints, copies)
        with (stage / "focused-near-copy-exclusions.jsonl").open("w", encoding="utf-8") as focused_exclusions:
            for row in sorted(targeted_excluded_origins, key=lambda item: (item["copyFamily"], item["corpus"], item["package"], item["path"])):
                focused_exclusions.write(dumps(row) + "\n")
        for sha in targeted_excluded_documents:
            db.execute("DELETE FROM documents WHERE hash=?", (sha,))
            for origin in provenance[sha]:
                if origin.get("focusedGenerator") == "targeted-go-feature-miner-v1":
                    corpus = origin["corpus"]
                    by_corpus[corpus]["heldoutNearCopyDocumentsExcluded"] = by_corpus[corpus].get("heldoutNearCopyDocumentsExcluded", 0) + 1
        counts["heldoutNearCopyDocumentsExcluded"] = len(targeted_excluded_documents)
        counts["heldoutNearCopyOriginsExcluded"] = len(targeted_excluded_origins)
        db.commit()

        excluded_components = {component for component, origins in copy_origins.items()
                               if len(origins) > 1 and any(not group.startswith("family:") for group in origins)}
        excluded = [sha for sha in provenance if copies.find(sha) in excluded_components]
        with (stage / "cross-group-copies.jsonl").open("w", encoding="utf-8") as excluded_file:
            for sha in sorted(excluded):
                excluded_file.write(dumps({"documentId": sha, "copyFamily": copies.find(sha),
                                          "reason": "cross-source-whole-document-copy", "provenance": provenance[sha]}) + "\n")
                db.execute("DELETE FROM documents WHERE hash=?", (sha,))
                for corpus in {origin["corpus"] for origin in provenance[sha]}:
                    by_corpus[corpus]["crossGroupCopyDocumentsExcluded"] = by_corpus[corpus].get("crossGroupCopyDocumentsExcluded", 0) + 1
        counts["crossGroupCopyDocumentsExcluded"] = len(excluded)
        counts["crossGroupCopyFamiliesExcluded"] = len(excluded_components)
        db.commit()
        weights = {group: weight for group, weight in db.execute(
            "SELECT group_id, SUM(weight) FROM documents WHERE stream='natural' GROUP BY group_id")}
        assignments = assign_groups(weights, seed)
        for group, values in hints.items():
            if len(values) != 1:
                raise ValueError(f"Focused family split conflict: {group}")
            assignments[group] = next(iter(values))
        group_report = [{"group": group, "split": assignments[group], "stream": stream,
                         "documents": documents, "fixedWindowWeight": weight}
                        for group, stream, documents, weight in db.execute(
                            "SELECT group_id, stream, COUNT(*), SUM(weight) FROM documents GROUP BY group_id, stream ORDER BY group_id")]
        (stage / "split-groups.json").write_text(json.dumps(group_report, indent=2) + "\n", encoding="utf-8")
        stats = {split: {"documents": 0, "windows": 0, "sourceBytes": 0, "spans": 0, "naturalWindows": 0, "focusWindows": 0,
                         "tokenTypes": Counter(), "naturalTokenTypes": Counter(), "focusTokenTypes": Counter(),
                         "modifiers": Counter(), "features": Counter(), "windowing": Counter()} for split in SPLITS}
        if weights:
            largest = max(weights.values())
            print(f"Natural source groups: {len(weights)}; largest fixed-window weight: {largest} ({largest / sum(weights.values()):.1%})", flush=True)
        print("Writing grouped splits and byte windows ...", flush=True)
        with ExitStack() as stack:
            docs, refs, columns = {}, {}, {}
            for split in SPLITS:
                folder = stage / split
                folder.mkdir()
                docs[split] = stack.enter_context((folder / "documents.jsonl").open("w", encoding="utf-8"))
                refs[split] = stack.enter_context((folder / "windows.jsonl").open("w", encoding="utf-8"))
                columns[split] = {name: stack.enter_context((folder / (name + ".bin")).open("wb")) for name in COLUMNS}
            for index, (sha, group, raw, stream_name) in enumerate(db.execute("SELECT hash,group_id,raw,stream FROM documents ORDER BY hash"), 1):
                record = json.loads(raw)
                split = assignments[group]
                encoded = encode(record, schema)
                window_refs, window_stats = windows(encoded, size, split == "train")
                group_id = digest(group.encode())
                info = stats[split]
                info["documents"] += 1
                info["spans"] += len(record["result"]["spans"])
                info["sourceBytes"] += len(encoded.columns["input_ids"])
                info["windowing"].update(window_stats)
                info["features"].update(features[sha])
                for span in record["result"]["spans"]:
                    info["tokenTypes"][span["tokenType"]] += 1
                    info[stream_name + "TokenTypes"][span["tokenType"]] += 1
                    info["modifiers"].update(span.get("modifiers", []))
                docs[split].write(dumps({**record, "id": sha, "groupId": group_id, "stream": stream_name,
                                        "features": sorted(features[sha]), "provenance": provenance[sha]}) + "\n")
                for lo, hi in window_refs:
                    row = padded_window(encoded, lo, hi, size)
                    for name, values in row.items():
                        columns[split][name].write(little_endian_bytes(values))
                    refs[split].write(dumps({"documentId": sha, "groupId": group_id, "startByte": lo, "endByte": hi,
                                            "length": hi - lo, "stream": stream_name}) + "\n")
                info["windows"] += len(window_refs)
                info["focusWindows" if stream_name == "focus" else "naturalWindows"] += len(window_refs)
                if index % 200 == 0:
                    print(f"  encoded {index} unique documents", flush=True)
        if any(not stats[s]["documents"] for s in SPLITS):
            raise ValueError("At least one grouped split is empty; add independent groups before training")
        balance = natural_balance({split: stats[split]["naturalWindows"] for split in SPLITS})
        checksums = {str(p.relative_to(stage)): file_hash(p) for p in sorted(stage.rglob("*")) if p.is_file() and p.name != "index.sqlite3"}
        missing_roles = {s: [t for t in schema.token_types if not stats[s]["tokenTypes"][t]] for s in SPLITS}
        return {
            "format": FORMAT, "snapshot": snapshot, "identity": identity, "contextBytes": size,
            "schema": {"tokenTypes": list(schema.token_types), "modifiers": list(schema.modifiers)},
            "columns": {name: {"typecode": code, "byteOrder": "little"} for name, code in COLUMNS.items()},
            "labels": {"padByteId": 256, "ignoreId": -100, "boundaryClasses": ["outside", "begin", "inside"],
                       "modifierSupervision": "span-beginnings", "continuationBytes": "ignored"},
            "policy": {"split": "size-balanced-source-groups-before-windowing", "naturalTargetRatios": [0.8, 0.1, 0.1],
                       "naturalGrouping": "whole-module-or-stdlib-subsystem",
                       "assignmentWeight": "character-safe-fixed-window-count",
                       "crossSourceCopies": "excluded-with-provenance-not-unioned-modules",
                       "trainWindowing": "gold-adaptive-cursor", "evaluationWindowing": "character-safe-fixed-cursor",
                       "focusSampling": "separate-stream-no-oversampling-yet", "nearCopies": "whole-document-lexical-and-alpha-shape",
                       "partialClones": "not-detected", "legacyGold": "syntax-proven-tilde-and-type-switch-repairs; remaining-gaps-quarantined"},
            "qualityGates": {"naturalSplitBalance": balance},
            "missingTokenTypesByStream": {stream: {split: [role for role in schema.token_types
                                                         if not stats[split][stream + "TokenTypes"][role]]
                                                  for split in SPLITS} for stream in ("natural", "focus")},
            "inputCounts": dict(counts), "corpora": by_corpus, "splits": stats, "missingTokenTypes": missing_roles,
            "checksums": checksums,
        }
    finally:
        db.close()
        database.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=dataset_root())
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--seed", type=int, default=1729)
    arguments = parser.parse_args()
    started = time.monotonic()
    try:
        report = build(arguments.root, arguments.config, arguments.root / "prepared", seed=arguments.seed)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Go dataset preparation failed: {error}\n")
    print("\nGo Training Dataset (512 UTF-8 bytes)")
    print(f"Snapshot: {report['snapshot'][:20]}")
    print(f"Input documents: {report['inputCounts'].get('inputDocuments', 0)}")
    print(f"Legacy tilde operator omissions repaired: {report['inputCounts'].get('repairedTildeOperators', 0)}")
    print(f"Type-switch declarations repaired: {report['inputCounts'].get('repairedTypeSwitchDeclarations', 0)}")
    print(f"Documents recovered by type-switch repair: {report['inputCounts'].get('recoveredTypeSwitchDocuments', 0)}")
    print(f"Exact duplicates removed: {report['inputCounts'].get('exactDuplicatesRemoved', 0)}")
    print(f"Targeted train near-copies of held-out focus excluded: {report['inputCounts'].get('heldoutNearCopyDocumentsExcluded', 0)}")
    print(f"Cross-source copy documents excluded: {report['inputCounts'].get('crossGroupCopyDocumentsExcluded', 0)}")
    print(f"Quarantined incomplete Gold documents: {report['inputCounts'].get('quarantinedDocuments', 0)}")
    for split, stats in report["splits"].items():
        print(f"{split}: {stats['documents']} documents, {stats['windows']} windows ({stats['naturalWindows']} natural + {stats['focusWindows']} focus)")
        print(f"  absent token types: {', '.join(report['missingTokenTypes'][split]) or 'none'}")
        print(f"  absent natural token types: {', '.join(report['missingTokenTypesByStream']['natural'][split]) or 'none'}")
    balance = report["qualityGates"]["naturalSplitBalance"]
    if balance["applicable"]:
        print("Natural window ratios: " + ", ".join(f"{key}={value:.1%}" for key, value in balance["ratios"].items()))
    print(f"Prepared in {time.monotonic() - started:.1f}s; pointer: {arguments.root / 'prepared/current.json'}")
    print("No model has been trained. Review manifest.json and quarantine.jsonl before baseline training.")


if __name__ == "__main__":
    main()
