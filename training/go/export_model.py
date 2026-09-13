"""Export a selected Go training checkpoint as the canonical inference artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import torch

from checkpoints import MODEL_FORMAT, atomic_json, load_checkpoint, save_checkpoint


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parameter_count(state: dict) -> int:
    return sum(int(value.numel()) for value in state.values() if torch.is_tensor(value))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("packs/go/model/model.pt"))
    parser.add_argument("--metadata", type=Path, default=Path("packs/go/model/model.json"))
    parser.add_argument("--test-report", type=Path)
    args = parser.parse_args()

    source = args.checkpoint.expanduser().resolve()
    checkpoint = load_checkpoint(source)
    if checkpoint["trainingConfig"].get("smoke"):
        raise ValueError("Smoke checkpoints cannot become the selected Go model")

    source_hash = sha256_file(source)
    report = None
    if args.test_report:
        report_path = args.test_report.expanduser().resolve()
        report = json.loads(report_path.read_text(encoding="utf-8"))
        expected_hash = report.get("checkpointHash")
        if expected_hash and expected_hash != source_hash:
            raise ValueError("Test report checkpoint hash does not match the selected checkpoint")

    artifact = {
        "format": MODEL_FORMAT,
        "model": checkpoint["model"],
        "modelConfig": checkpoint["modelConfig"],
        "schema": checkpoint["schema"],
        "dataset": checkpoint["dataset"],
        "trainingConfig": {
            "modifier_threshold": checkpoint["trainingConfig"]["modifier_threshold"],
        },
        "epoch": checkpoint["epoch"],
        "validation": checkpoint.get("validation"),
        "provenance": {
            "sourceCheckpointSha256": source_hash,
            "sourceCheckpoint": str(source),
        },
    }

    output = args.output.expanduser()
    save_checkpoint(output, artifact)
    output_hash = sha256_file(output)

    metadata = {
        "id": "go",
        "artifact": {
            "file": output.name,
            "format": MODEL_FORMAT,
            "sha256": output_hash,
            "bytes": output.stat().st_size,
            "parameterCount": parameter_count(artifact["model"]),
            "containsOptimizerState": False,
            "resumableTrainingCheckpoint": False,
        },
        "selection": {
            "epoch": checkpoint["epoch"],
            "basis": "selected training checkpoint promoted after pure-neural evaluation and Playground verification",
        },
        "checkpointConfig": checkpoint["modelConfig"],
        "orderedLabels": {
            "boundary": ["O", "B", "I"],
            "tokenTypes": checkpoint["schema"]["tokenTypes"],
            "modifiers": checkpoint["schema"]["modifiers"],
        },
        "input": {
            "encoding": "utf-8",
            "unit": "byte",
            "vocabSize": 257,
            "paddingId": 256,
            "maxLengthBytes": checkpoint["modelConfig"]["context_bytes"],
        },
        "output": {
            "offsetEncoding": "utf-16",
            "interval": "[start,end)",
            "contract": "../SEMANTICS.md",
        },
        "inference": {
            "windowing": "predicted-adaptive-cursor",
            "decoder": "greedy",
            "modifierThreshold": checkpoint["trainingConfig"]["modifier_threshold"],
            "goToolchainRequired": False,
        },
        "dataset": checkpoint["dataset"],
        "provenance": {
            "sourceCheckpoint": str(source),
            "sourceCheckpointSha256": source_hash,
        },
    }

    if report is not None:
        reports_dir = output.parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_target = reports_dir / "test-metrics.json"
        shutil.copyfile(args.test_report.expanduser(), report_target)
        metadata["reports"] = {
            "test-metrics.json": {
                "file": "reports/test-metrics.json",
                "sha256": sha256_file(report_target),
                "checkpointHash": report.get("checkpointHash"),
                "split": report.get("split"),
                "inference": report.get("inference"),
            }
        }

    atomic_json(args.metadata.expanduser(), metadata)
    print(f"Go model exported: {output}")
    print(f"Metadata: {args.metadata.expanduser()}")
    print(f"SHA256: {output_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
