"""Prepare immutable pack byte datasets from the existing external Gold corpus."""
from __future__ import annotations

from training.shared.spec import current

import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from training.shared.encoding import COLUMNS, Schema, encode, little_endian_bytes, padded_window, windows
from training.shared.io import atomic_json, training_lock

REPOSITORY = Path(__file__).resolve().parents[2]
SPLITS = ("train", "validation", "test")


def file_hash(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            checksum.update(block)
    return checksum.hexdigest()


def dumps(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def dataset_root() -> Path:
    return Path(os.environ.get("NSH_DATASET_ROOT", "~/Datasets/neural-semantic-highlighting")).expanduser() / current().id


def assign_groups(weights: dict[str, Counter], seed: int) -> dict[str, str]:
    """Balance profile/stream coverage while keeping each directory family intact."""
    axes = sorted({kind for value in weights.values() for kind in value})
    totals = {kind: sum(value[kind] for value in weights.values()) for kind in axes}
    for kind in axes:
        if sum(bool(value[kind]) for value in weights.values()) < 3:
            raise ValueError(f"{kind} needs at least three independent source groups after deduplication")
    ratios = (.8, .1, .1)
    loads = [Counter(), Counter(), Counter()]
    groups = [set(), set(), set()]
    targets = [{kind: max(1., totals[kind] * ratio) for kind in axes} for ratio in ratios]
    def error(index: int, values: Counter) -> float:
        return sum((values[kind] - targets[index][kind]) ** 2 / targets[index][kind] for kind in axes)
    ordered = sorted(weights, key=lambda group: (-sum(weights[group].values()),
        hashlib.sha256(f"{seed}:{group}".encode()).hexdigest()))
    assigned = {}
    for group in ordered:
        size = weights[group]
        index = min(range(3), key=lambda i: (error(i, loads[i] + size) - error(i, loads[i]), i))
        assigned[group] = index
        loads[index].update(size)
        groups[index].add(group)
    # Greedy ratio fitting can leave a rare profile absent even with enough
    # independent groups. Repair coverage before ratio optimization, without
    # removing the last source of any already represented axis from a donor.
    for index in range(3):
        for kind in axes:
            if loads[index][kind]:
                continue
            candidates = [group for group in ordered if weights[group][kind] and assigned[group] != index
                          and all(not weights[group][axis] or loads[assigned[group]][axis] > weights[group][axis]
                                  for axis in axes)]
            if not candidates:
                raise ValueError("Cannot preserve intact-group coverage for " + kind)
            def cost(group):
                old, size = assigned[group], weights[group]
                return error(old, loads[old] - size) + error(index, loads[index] + size) - error(old, loads[old]) - error(index, loads[index])
            group = min(candidates, key=cost)
            old, size = assigned[group], weights[group]
            loads[old].subtract(size); groups[old].remove(group)
            assigned[group] = index; loads[index].update(size); groups[index].add(group)
    # Move intact groups only. A source containing both kinds is never split.
    for _ in range(32):
        changed = False
        for group in ordered:
            old, size = assigned[group], weights[group]
            if any(size[kind] and loads[old][kind] <= size[kind] for kind in axes):
                continue
            best, delta = old, -1e-9
            for new in range(3):
                if old == new:
                    continue
                value = (error(old, loads[old] - size) + error(new, loads[new] + size)
                         - error(old, loads[old]) - error(new, loads[new]))
                if value < delta:
                    best, delta = new, value
            if best != old:
                loads[old].subtract(size)
                loads[best].update(size)
                groups[old].remove(group)
                groups[best].add(group)
                assigned[group] = best
                changed = True
        if not changed:
            break
    for index in range(3):
        for kind in axes:
            if not loads[index][kind]:
                raise ValueError(f"Grouped allocation has no {kind} in {SPLITS[index]}; add independent sources")
    return {group: SPLITS[index] for group, index in assigned.items()}


def prepare(root: Path, *, seed: int = 1729, groups_file: Path | None = None) -> dict:
    root = root.expanduser().resolve()
    output = root / "prepared"
    output.mkdir(parents=True, exist_ok=True)
    with training_lock(output):
        pointer = json.loads((root / "current-gold.json").read_text())
        folder = (root / pointer["directory"]).resolve()
        if not folder.is_relative_to(root) or folder == root:
            raise ValueError("Unsafe Gold pointer")
        if file_hash(folder / "sample.json") != pointer["manifestHash"]:
            raise ValueError("Gold manifest checksum mismatch")
        manifest = json.loads((folder / "sample.json").read_text())
        for name, expected in manifest["checksums"].items():
            path = folder / name
            if not path.resolve().is_relative_to(folder) or file_hash(path) != expected:
                raise ValueError("Gold checksum mismatch")
        schema_path = current().schema_path
        schema = Schema.load(schema_path)
        if manifest["provenance"]["schemaHash"] != file_hash(schema_path):
            raise ValueError("Gold schema changed; create a new Gold snapshot")
        semantic_hash = file_hash(current().semantics_path)
        if manifest["provenance"].get("semanticContractHash") != semantic_hash:
            raise ValueError("Gold semantic contract changed; create a new Gold snapshot")
        builder_hashes = {name: file_hash(Path(__file__).with_name(name))
                          for name in ("prepare.py", "encoding.py", "spec.py")}
        groups_file = groups_file or current().directory / "dataset/split-groups.json"
        frozen_groups = json.loads(groups_file.read_text())
        if frozen_groups.get("format") != f"nsh-{current().id}-split-groups-v1" or any(value not in SPLITS for value in frozen_groups["assignments"].values()):
            raise ValueError("Invalid frozen pack source-family assignments")
        identity = {"format": current().dataset_format, "gold": pointer["manifestHash"], "schema": file_hash(schema_path),
                    "builders": builder_hashes, "fixedGroupsHash": file_hash(groups_file),
                    "contextBytes": 512, "seed": seed, "semanticContractHash": semantic_hash}
        snapshot = hashlib.sha256(dumps(identity).encode()).hexdigest()
        target = output / snapshot
        if target.exists():
            existing = json.loads((target / "manifest.json").read_text())
            for name, expected in existing["checksums"].items():
                if file_hash(target / name) != expected:
                    raise ValueError("Existing immutable snapshot is corrupt")
            atomic_json(output / "current.json", {"snapshotDirectory": snapshot})
            return existing

        records = {}
        fingerprints = defaultdict(set)
        for line in (folder / "labeled-sample.jsonl").read_text().splitlines():
            if not line:
                continue
            record = json.loads(line)
            encoded = encode(record, schema)
            doc_id = hashlib.sha256((record["documentKind"] + ":" + record["contentHash"]).encode()).hexdigest()
            if doc_id in records:
                if records[doc_id]["result"] != record["result"]:
                    raise ValueError("Conflicting Gold for identical source")
                records[doc_id]["origins"].append({key: record[key] for key in ("repository", "path", "sourceGroup")})
            else:
                records[doc_id] = {**record, "id": doc_id, "stream": record.get("stream", "natural"),
                    "origins": [{key: record[key] for key in ("repository", "path", "sourceGroup")}]}
            for label, value in (("exact", record["contentHash"]), ("lexical", encoded.normalized_hash),
                                 ("shape", encoded.shape_hash)):
                fingerprints[(label, value)].add(doc_id)
        if len(records) > manifest["files"]:
            raise ValueError("Invalid Gold document count")
        # Exclude copies crossing source groups, rather than joining unrelated
        # projects or letting renamed/template siblings leak across holdouts.
        excluded = set()
        copy_audit = []
        for (kind, value), members in sorted(fingerprints.items()):
            source_groups = {origin["sourceGroup"] for name in members for origin in records[name]["origins"]}
            if len(source_groups) > 1:
                excluded.update(members)
                copy_audit.append({"kind": kind, "fingerprint": value,
                    "documents": sorted(members), "sourceGroups": sorted(source_groups)})
        weights: dict[str, Counter] = defaultdict(Counter)
        for name, record in records.items():
            if name in excluded:
                continue
            groups = {origin["sourceGroup"] for origin in record["origins"]}
            if len(groups) != 1:
                raise ValueError("Cross-group copies were not excluded")
            record["sourceGroup"] = next(iter(groups))
            fixed, _ = windows(encode(record, schema), 512, adaptive=False)
            weights[record["sourceGroup"]][record["documentKind"] + ":" + record["stream"]] += len(fixed)
            weights[record["sourceGroup"]]["profile:" + record["profile"] + ":" + record["stream"]] += len(fixed)
        assignments = assign_groups(dict(weights), seed)
        assignments.update({group: split for group, split in frozen_groups["assignments"].items() if group in weights})
        for split in SPLITS:
            for axis in {axis for value in weights.values() for axis in value}:
                if not any(counts[axis] for group, counts in weights.items() if assignments[group] == split):
                    raise ValueError("Frozen groups leave missing coverage: " + split + ":" + axis)
        for profile in current().profiles:
            for stream in ("natural", "focus"):
                axis = "profile:" + profile + ":" + stream
                if len([group for group, counts in weights.items() if counts[axis]]) < 3:
                    raise ValueError("Need three independent retained groups for " + axis)
        staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=output))
        try:
            statistics = {}
            with ExitStack() as stack:
                for split in SPLITS:
                    directory = staging / split
                    directory.mkdir()
                    docs = stack.enter_context((directory / "documents.jsonl").open("w"))
                    refs = stack.enter_context((directory / "windows.jsonl").open("w"))
                    columns = {name: stack.enter_context((directory / (name + ".bin")).open("wb")) for name in COLUMNS}
                    counts = Counter(documents=0, windows=0, naturalWindows=0, focusWindows=0)
                    kind_counts = {kind: Counter(documents=0, windows=0, spans=0) for kind in current().document_kinds}
                    role_counts = {kind: Counter() for kind in current().document_kinds}
                    for name, record in sorted(records.items()):
                        if name in excluded or assignments[record["sourceGroup"]] != split:
                            continue
                        encoded = encode(record, schema)
                        ranges, _ = windows(encoded, 512, adaptive=split == "train")
                        docs.write(dumps(record) + "\n")
                        counts.update(documents=1, windows=len(ranges), **{record["stream"] + "Windows": len(ranges)})
                        kind_counts[record["documentKind"]].update(documents=1, windows=len(ranges),
                            spans=len(record["result"]["spans"]))
                        role_counts[record["documentKind"]].update(span["tokenType"] for span in record["result"]["spans"])
                        for lo, hi in ranges:
                            refs.write(dumps({"documentId": name, "stream": record.get("stream", "natural"), "documentKind": record["documentKind"],
                                "startByte": lo, "endByte": hi, "length": hi - lo}) + "\n")
                            for column, values in padded_window(encoded, lo, hi, 512).items():
                                columns[column].write(little_endian_bytes(values))
                    statistics[split] = {**counts, "documentKinds": kind_counts, "tokenTypes": role_counts}
            (staging / "cross-group-copies.jsonl").write_text("".join(dumps(item) + "\n" for item in copy_audit))
            (staging / "split-groups.json").write_text(dumps(assignments) + "\n")
            checksums = {str(path.relative_to(staging)): file_hash(path) for path in sorted(staging.rglob("*")) if path.is_file()}
            result = {"format": current().dataset_format, "snapshot": snapshot, "contextBytes": 512, "identity": identity,
                "schema": {"tokenTypes": list(schema.token_types), "modifiers": list(schema.modifiers)},
                "labels": {"padByteId": 256, "ignoreId": -100, "boundaryClasses": ["outside", "begin", "inside"],
                    "modifierSupervision": "span-beginnings", "continuationBytes": "ignored"},
                "policy": {"split": "intact-source-directories-before-windowing",
                    "trainingWindowing": "gold-adaptive-cursor", "evaluationWindowing": "character-safe-fixed-cursor",
                    "crossGroupCopies": "excluded", "targetRatios": [.8, .1, .1], "balanceAxes": "document-kind-stream-and-profile",
                    "fixedSourceGroupsHash": file_hash(groups_file)},
                "inputDocuments": manifest["files"], "uniqueDocuments": len(records),
                "exactDuplicateRecords": manifest["files"] - len(records), "excludedCopyDocuments": len(excluded),
                "retainedDocuments": sum(value["documents"] for value in statistics.values()),
                "splits": statistics, "checksums": checksums}
            atomic_json(staging / "manifest.json", result)
            staging.rename(target)
            atomic_json(output / "current.json", {"snapshotDirectory": snapshot})
            return result
        finally:
            if staging.exists():
                shutil.rmtree(staging)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=dataset_root(), help="pack dataset directory, not its parent")
    parser.add_argument("--groups-file", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.root, groups_file=args.groups_file), indent=2))


if __name__ == "__main__":
    main()
