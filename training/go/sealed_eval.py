"""One-time external blind acceptance evaluation for the Go semantic model.

The sealed corpora are never prepared as train/validation/test windows. This
script reads their package-aware Gold JSONL directly and runs predicted adaptive
runtime inference. A successful evaluation writes a permanent seal marker and
refuses a second run so this set cannot quietly become another tuning loop.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

import torch

from checkpoints import atomic_json, load_checkpoint, model_from_checkpoint, select_device
from encoding import Schema, encode
from inference import decode, document_logits
from metrics import SpanMetrics
from quality import TARGET_F1, TARGETED_ROLES
from trainer_data import sha256_file

REPOSITORY = Path(__file__).resolve().parents[2]
SEALED_CONFIG = REPOSITORY / "packs/go/dataset/sources/sealed.json"
TRAINING_CONFIG = REPOSITORY / "training/go/corpora.json"
SCHEMA_PATH = REPOSITORY / "packs/go/schema.json"
FOCUS_ID = "sealed-modern-v1"
FOCUS_PROFILE = "sealed-v1"
GOLD_TOOLCHAIN = "go1.27.1"
SEAL_VERSION = 1
MIN_ROLE_SUPPORT = 32
MIN_TARGET_SUPPORT = 32
MIN_NATURAL_EXACT_F1 = 0.95
MIN_NATURAL_MACRO_F1 = 0.90
MIN_MODIFIED_EXACT_F1 = 0.95
MIN_FOCUS_EXACT_F1 = 0.98
MAX_ERROR_EXAMPLES_PER_STREAM = 40


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def dataset_root() -> Path:
    parent = Path(os.environ.get("NSH_DATASET_ROOT", "~/Datasets/neural-semantic-highlighting")).expanduser()
    return parent / "go"


def read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"Blank JSONL record: {path}:{line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"Non-object JSONL record: {path}:{line_number}")
            records.append(value)
    return records


def training_content_hashes(root: Path) -> tuple[set[str], set[str]]:
    config = load_json(TRAINING_CONFIG)
    hashes: set[str] = set()
    modules: set[str] = set()
    for spec in config.get("sources", []):
        source_id = str(spec.get("id", ""))
        if source_id.startswith("sealed-"):
            raise ValueError(f"Training configuration illegally contains sealed corpus {source_id}")
        if spec.get("kind") == "module":
            modules.add(str(spec.get("module", "")))
        folder = (root / spec["directory"]).resolve()
        gold = folder / "labeled-sample.jsonl"
        if not gold.is_file():
            raise ValueError(f"Training provenance corpus is missing: {gold}")
        for record in read_jsonl(gold):
            content_hash = record.get("contentHash")
            if not isinstance(content_hash, str):
                raise ValueError(f"Training corpus has missing content hash: {gold}")
            hashes.add(content_hash)
    return hashes, modules


def validate_records(records: list[dict], schema: Schema, *, expected_stream: str,
                     training_hashes: set[str], seen_hashes: set[str]) -> None:
    for record in records:
        content_hash = record.get("contentHash")
        if not isinstance(content_hash, str):
            raise ValueError("Sealed record lacks contentHash")
        if content_hash in training_hashes:
            raise ValueError(f"Sealed exact-source leakage into training data: {record.get('path')}")
        if content_hash in seen_hashes:
            raise ValueError(f"Duplicate source inside sealed set: {record.get('path')}")
        seen_hashes.add(content_hash)
        encode(record, schema)  # validates UTF-16 Gold, completeness, role ids, and source hash
        if expected_stream == "focus":
            if record.get("split") != "sealed":
                raise ValueError(f"Sealed focus record has split {record.get('split')!r}")
            features = record.get("features")
            if not isinstance(features, list) or len(features) != 1 or features[0] not in TARGETED_ROLES:
                raise ValueError(f"Unexpected sealed focus features: {features!r}")


def load_sealed_data(root: Path, schema: Schema) -> tuple[list[dict], list[dict], dict]:
    config = load_json(SEALED_CONFIG)
    if config.get("formatVersion") != 1 or not config.get("sources"):
        raise ValueError("Invalid sealed module configuration")
    training_hashes, training_modules = training_content_hashes(root)
    seen_hashes: set[str] = set()
    natural: list[dict] = []
    resolved_sources: list[dict] = []
    for spec in config["sources"]:
        source_id = spec.get("id")
        module = spec.get("module")
        if not isinstance(source_id, str) or not source_id.startswith("sealed-"):
            raise ValueError(f"Sealed module id must start with sealed-: {source_id!r}")
        if module in training_modules:
            raise ValueError(f"Sealed module identity already appears in training: {module}")
        folder = root / "corpora" / source_id
        sample_path = folder / "sample.json"
        gold_path = folder / "labeled-sample.jsonl"
        lock_path = folder / "source.lock.json"
        for path in (sample_path, gold_path, lock_path, folder / "statistics.json"):
            if not path.is_file():
                raise ValueError(f"Missing sealed module artifact: {path}; run make dataset-go-sealed first")
        sample = load_json(sample_path)
        lock = load_json(lock_path)
        if sample.get("toolchain") != GOLD_TOOLCHAIN or sample.get("corpus") != source_id:
            raise ValueError(f"Wrong sealed module toolchain/identity: {source_id}")
        source = sample.get("source", {})
        if source.get("module") != module or not source.get("version") or not source.get("sum"):
            raise ValueError(f"Unpinned sealed module source: {source_id}")
        if lock.get("source") != source:
            raise ValueError(f"Sealed module source lock differs from sample manifest: {source_id}")
        records = read_jsonl(gold_path)
        if len(records) != len(sample.get("files", [])):
            raise ValueError(f"Sealed module Gold count differs from manifest: {source_id}")
        validate_records(records, schema, expected_stream="natural", training_hashes=training_hashes,
                         seen_hashes=seen_hashes)
        for record in records:
            record["_sealedSource"] = source_id
        natural.extend(records)
        resolved_sources.append({
            "id": source_id,
            "module": module,
            "version": source["version"],
            "sum": source["sum"],
            "goModSum": source.get("goModSum"),
            "files": len(records),
            "sampleHash": sha256_file(sample_path),
            "goldHash": sha256_file(gold_path),
            "lockHash": sha256_file(lock_path),
        })

    focus_folder = root / "curricula" / FOCUS_ID
    focus_sample = focus_folder / "sample.json"
    focus_gold = focus_folder / "labeled-sample.jsonl"
    if not focus_sample.is_file() or not focus_gold.is_file():
        raise ValueError(f"Missing sealed focused corpus {FOCUS_ID}; run make dataset-go-sealed first")
    focus_manifest = load_json(focus_sample)
    if (focus_manifest.get("toolchain") != GOLD_TOOLCHAIN or focus_manifest.get("corpus") != FOCUS_ID
            or focus_manifest.get("kind") != "focused" or focus_manifest.get("profile") != FOCUS_PROFILE
            or focus_manifest.get("generator") != "sealed-go-acceptance-v1"):
        raise ValueError("Sealed focused manifest identity differs from the acceptance profile")
    focus = read_jsonl(focus_gold)
    if len(focus) != len(focus_manifest.get("files", [])):
        raise ValueError("Sealed focused Gold count differs from manifest")
    validate_records(focus, schema, expected_stream="focus", training_hashes=training_hashes,
                     seen_hashes=seen_hashes)
    for record in focus:
        record["_sealedSource"] = FOCUS_ID

    identity = {
        "formatVersion": SEAL_VERSION,
        "modulesConfigHash": sha256_file(SEALED_CONFIG),
        "trainingConfigHash": sha256_file(TRAINING_CONFIG),
        "schemaHash": sha256_file(SCHEMA_PATH),
        "modules": resolved_sources,
        "focus": {
            "id": FOCUS_ID,
            "profile": FOCUS_PROFILE,
            "files": len(focus),
            "sampleHash": sha256_file(focus_sample),
            "goldHash": sha256_file(focus_gold),
        },
    }
    identity["sealHash"] = hashlib.sha256(canonical(identity)).hexdigest()
    return natural, focus, identity


def utf16_slice(source: str, start: int, end: int) -> str:
    units = 0
    left = right = None
    for index, char in enumerate(source):
        if units == start and left is None:
            left = index
        units += 2 if ord(char) > 0xFFFF else 1
        if units == end:
            right = index + 1
            break
    if left is None:
        left = len(source)
    if right is None:
        right = len(source)
    return source[left:right]


def mismatch_rows(record: dict, predicted: dict, *, limit: int) -> list[dict]:
    def key(span: dict) -> tuple:
        return (span["start"], span["end"], span["tokenType"], tuple(sorted(span.get("modifiers", []))))

    gold = {key(span): span for span in record["result"]["spans"]}
    pred = {key(span): span for span in predicted["spans"]}
    rows: list[dict] = []
    for kind, values in (("false-negative", sorted(set(gold) - set(pred))),
                         ("false-positive", sorted(set(pred) - set(gold)))):
        for value in values:
            if len(rows) >= limit:
                return rows
            span = gold.get(value) or pred[value]
            rows.append({
                "kind": kind,
                "source": record["_sealedSource"],
                "package": record.get("package"),
                "path": record.get("path"),
                "feature": (record.get("features") or [None])[0],
                "span": span,
                "text": utf16_slice(record["source"], span["start"], span["end"]),
            })
    return rows


def role_gate(report: dict) -> dict:
    rows = []
    checked = []
    low_support = []
    for role, metrics in report["byTokenType"].items():
        support = int(metrics["support"])
        f1 = float(metrics["f1"])
        if support == 0:
            status = "UNREPRESENTED"
        elif support < MIN_ROLE_SUPPORT:
            status = "LOW_SUPPORT"
            low_support.append(role)
        elif f1 >= TARGET_F1:
            status = "PASS"
            checked.append(True)
        else:
            status = "FAIL"
            checked.append(False)
        rows.append({"role": role, "support": support, "f1": f1, "status": status})
    return {
        "threshold": TARGET_F1,
        "minimumSupport": MIN_ROLE_SUPPORT,
        "passed": bool(checked) and all(checked),
        "checkedRoles": sum(1 for row in rows if row["status"] in {"PASS", "FAIL"}),
        "lowSupportRoles": low_support,
        "roles": rows,
    }


def targeted_gate(features: dict[str, dict]) -> dict:
    rows = []
    for feature, role in TARGETED_ROLES.items():
        metrics = features.get(feature, {}).get("byTokenType", {}).get(role, {})
        support = int(metrics.get("support", 0))
        f1 = float(metrics.get("f1", 0.0))
        passed = support >= MIN_TARGET_SUPPORT and f1 >= TARGET_F1
        rows.append({"feature": feature, "role": role, "support": support, "f1": f1, "passed": passed})
    return {
        "threshold": TARGET_F1,
        "minimumSupport": MIN_TARGET_SUPPORT,
        "passed": all(row["passed"] for row in rows),
        "roles": rows,
    }


@torch.inference_mode()
def evaluate_records(model, device: torch.device, schema: dict, threshold: float,
                     natural: list[dict], focus: list[dict]) -> tuple[dict, dict[str, list[dict]]]:
    natural_metrics = SpanMetrics(schema)
    focus_metrics = SpanMetrics(schema)
    source_metrics: dict[str, SpanMetrics] = {}
    feature_metrics: dict[str, SpanMetrics] = {}
    errors: dict[str, list[dict]] = {"natural": [], "focus": []}
    documents = [("natural", record) for record in natural] + [("focus", record) for record in focus]
    started = time.monotonic()
    for index, (stream, record) in enumerate(documents, 1):
        output = document_logits(model, record["source"], device, adaptive=True)
        predicted = decode(record["source"], output, schema, threshold=threshold)
        if stream == "natural":
            natural_metrics.add(record["result"], predicted)
            source_metrics.setdefault(record["_sealedSource"], SpanMetrics(schema)).add(record["result"], predicted)
        else:
            focus_metrics.add(record["result"], predicted)
            for feature in record.get("features", []):
                feature_metrics.setdefault(feature, SpanMetrics(schema)).add(record["result"], predicted)
        if len(errors[stream]) < MAX_ERROR_EXAMPLES_PER_STREAM:
            errors[stream].extend(
                mismatch_rows(record, predicted, limit=MAX_ERROR_EXAMPLES_PER_STREAM - len(errors[stream]))
            )
        if index == 1 or index % 25 == 0 or index == len(documents):
            elapsed = time.monotonic() - started
            rate = index / elapsed if elapsed else 0.0
            remaining = (len(documents) - index) / rate if rate else 0.0
            print(f"sealed {index:4d}/{len(documents)} documents {rate:.1f} doc/s ETA={remaining:05.0f}s", flush=True)
    return {
        "inference": "predicted-adaptive-runtime",
        "seconds": time.monotonic() - started,
        "streams": {"natural": natural_metrics.report(), "focus": focus_metrics.report()},
        "naturalSources": {name: metrics.report() for name, metrics in sorted(source_metrics.items())},
        "focusFeatures": {name: metrics.report() for name, metrics in sorted(feature_metrics.items())},
    }, errors


def acceptance(report: dict) -> dict:
    natural = report["streams"]["natural"]
    focus = report["streams"]["focus"]
    roles = role_gate(natural)
    targeted = targeted_gate(report["focusFeatures"])
    checks = {
        "naturalExactSpanF1": {"minimum": MIN_NATURAL_EXACT_F1, "value": natural["exactSpan"]["f1"]},
        "naturalMacroF1": {"minimum": MIN_NATURAL_MACRO_F1, "value": natural["exactSpanMacroF1"]},
        "naturalExactSpanIncludingModifiersF1": {"minimum": MIN_MODIFIED_EXACT_F1,
                                                  "value": natural["exactSpanIncludingModifiers"]["f1"]},
        "focusExactSpanF1": {"minimum": MIN_FOCUS_EXACT_F1, "value": focus["exactSpan"]["f1"]},
    }
    numeric_passed = all(item["value"] >= item["minimum"] for item in checks.values())
    return {
        "passed": numeric_passed and roles["passed"] and targeted["passed"],
        "checks": checks,
        "naturalRoleGate": roles,
        "targetedRoleGate": targeted,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "mps", "cuda", "cpu"], default="auto")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        root = dataset_root()
        marker = root / "sealed" / "opened-v1.json"
        if marker.exists():
            previous = load_json(marker)
            raise ValueError(
                "The Go sealed-v1 set has already been opened. Do not rerun or tune against it. "
                f"Previous checkpoint: {previous.get('checkpointHash', 'unknown')}"
            )
        checkpoint = load_checkpoint(args.checkpoint)
        if checkpoint["trainingConfig"].get("smoke"):
            raise ValueError("Do not spend the sealed acceptance set on a smoke checkpoint")
        file_schema = Schema.load(SCHEMA_PATH)
        schema = checkpoint["schema"]
        if schema != {"tokenTypes": list(file_schema.token_types), "modifiers": list(file_schema.modifiers)}:
            raise ValueError("Checkpoint schema differs from the current Go semantic schema")
        natural, focus, seal_identity = load_sealed_data(root, file_schema)
        device = select_device(args.device)
        if device.type == "cpu":
            torch.set_num_threads(min(8, torch.get_num_threads()))
        model = model_from_checkpoint(checkpoint, device)
        threshold = float(checkpoint["trainingConfig"]["modifier_threshold"])
        print("Neural Semantic Highlighting")
        print("Go Sealed Blind Acceptance v1")
        print(f"Seal:       {seal_identity['sealHash'][:20]}")
        print(f"Checkpoint: {args.checkpoint.expanduser().resolve()}")
        print(f"Natural:    {len(natural)} documents across {len(seal_identity['modules'])} unseen modules")
        print(f"Focused:    {len(focus)} documents across {len(TARGETED_ROLES)} unseen structural features")
        print("This evaluation is one-time. A completed run permanently marks sealed-v1 as opened.")
        metrics, errors = evaluate_records(model, device, schema, threshold, natural, focus)
        gate = acceptance(metrics)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        output = args.output or args.checkpoint.expanduser().resolve().parent / f"sealed-blind-v1-{stamp}.json"
        result = {
            "format": "nsh-go-sealed-evaluation-v1",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "seal": seal_identity,
            "checkpoint": {
                "path": str(args.checkpoint.expanduser().resolve()),
                "hash": sha256_file(args.checkpoint.expanduser()),
                "epoch": checkpoint["epoch"],
                "dataset": checkpoint["dataset"],
            },
            **metrics,
            "acceptance": gate,
            "errorExamples": errors,
        }
        atomic_json(output, result)
        atomic_json(marker, {
            "formatVersion": SEAL_VERSION,
            "openedAt": result["createdAt"],
            "sealHash": seal_identity["sealHash"],
            "checkpointHash": result["checkpoint"]["hash"],
            "report": str(output),
            "passed": gate["passed"],
        })

        natural_report = metrics["streams"]["natural"]
        focus_report = metrics["streams"]["focus"]
        print("\nSealed natural")
        print(f"  exact-span F1:             {natural_report['exactSpan']['f1']:.4f}")
        print(f"  exact-span macro F1:       {natural_report['exactSpanMacroF1']:.4f}")
        print(f"  including modifiers F1:    {natural_report['exactSpanIncludingModifiers']['f1']:.4f}")
        print("  role gate (support >= 32):")
        for row in gate["naturalRoleGate"]["roles"]:
            if row["support"]:
                print(f"    {row['role']:<16} {row['f1']:.4f} support={row['support']:<6} {row['status']}")
        print("\nSealed focused")
        print(f"  exact-span F1:             {focus_report['exactSpan']['f1']:.4f}")
        print(f"  exact-span macro F1:       {focus_report['exactSpanMacroF1']:.4f}")
        print("  targeted role gate:")
        for row in gate["targetedRoleGate"]["roles"]:
            status = "PASS" if row["passed"] else "FAIL"
            print(f"    {row['feature']} / {row['role']}: {row['f1']:.4f} (support {row['support']}) {status}")
        print(f"\nSEALED ACCEPTANCE: {'PASS' if gate['passed'] else 'FAIL'}")
        print(f"Report: {output}")
        print(f"Seal marker: {marker}")
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, json.JSONDecodeError) as error:
        print(f"Go sealed evaluation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
