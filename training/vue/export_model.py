"""Promote a reviewed Vue checkpoint with a matching independent adaptive test report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from training.portable import portable_data

from training.vue.checkpoints import MODEL_FORMAT, atomic_json, load_checkpoint, save_checkpoint
from training.vue.prepare import REPOSITORY, file_hash

KINDS = ("vue",)


def export_model(source: Path, test_report: Path, output: Path) -> dict:
    source_hash = file_hash(source)
    checkpoint = load_checkpoint(source)
    if file_hash(source) != source_hash:
        raise ValueError("Checkpoint changed while loading; export a frozen checkpoint")
    if checkpoint["trainingConfig"].get("smoke"):
        raise ValueError("Smoke checkpoints cannot become a selected Vue model")
    if checkpoint["modelConfig"]["context_bytes"] != 512 or checkpoint.get("documentKinds") != list(KINDS):
        raise ValueError("Expected the Vue baseline configuration")
    report = json.loads(test_report.read_text())
    identity = {key: checkpoint["dataset"][key] for key in ("snapshot", "manifestHash")}
    if (report.get("split") != "test" or report.get("inference") != "predicted-adaptive-cursor"
            or report.get("checkpointHash") != source_hash or report.get("checkpointEpoch") != checkpoint["epoch"]
            or report.get("dataset") != identity or report.get("smokeCheckpoint") is not False
            or report.get("modelConfig") != checkpoint["modelConfig"]):
        raise ValueError("A matching held-out adaptive test report is required")
    if any(report.get("documentKinds", {}).get(kind, {}).get("documents", 0) < 1 for kind in KINDS):
        raise ValueError("Every Vue document kind needs independent test evidence")
    if any(report.get("profiles", {}).get(profile, {}).get("natural", {}).get("documents", 0) < 1
           for profile in ("vue2", "vue3", "vue3.2")):
        raise ValueError("Every Vue coverage profile needs real-source independent test evidence")
    if report.get("scope") != "base-vue-markup-and-neural-regions" or "bodyRegions" not in report:
        raise ValueError("Explicit base-model scope and body-region evidence are required")
    if checkpoint["provenance"]["semanticsHash"] != file_hash(REPOSITORY / "packs/vue/SEMANTICS.md"):
        raise ValueError("Checkpoint semantic contract differs from the current pack")
    if output.resolve() in {source.resolve(), test_report.resolve()}:
        raise ValueError("Export must preserve the original checkpoint and report")
    if output.exists():
        raise ValueError("Export target already exists; preserve the previous selected model bundle")
    for document in ("README.md", "BENCHMARKS.md", "KNOWN_ISSUES.md"):
        if not (output.parent / document).is_file():
            raise ValueError("Prepare the reviewed model documentation before export: " + document)
    artifact = {"format": MODEL_FORMAT, "model": checkpoint["model"], "modelConfig": checkpoint["modelConfig"],
        "schema": checkpoint["schema"], "dataset": checkpoint["dataset"], "epoch": checkpoint["epoch"],
        "documentKinds": list(KINDS),
        "trainingConfig": {"modifier_threshold": checkpoint["trainingConfig"]["modifier_threshold"]},
        "validation": checkpoint["validation"], "provenance": checkpoint["provenance"],
        "initialization": checkpoint.get("initialization")}
    artifact = portable_data(artifact)
    save_checkpoint(output, artifact)
    # Verify the stored float32 tensors; export performs no quantization/retraining.
    reloaded = torch.load(output, map_location="cpu", weights_only=True)
    if set(reloaded["model"]) != set(checkpoint["model"]) or any(
        not torch.equal(value.cpu(), reloaded["model"][name]) for name, value in checkpoint["model"].items()):
        raise ValueError("Export changed model weights")
    reports = output.parent / "reports"
    reports.mkdir(exist_ok=True)
    report_target = reports / "test-metrics.json"
    if report_target.resolve() != test_report.resolve():
        atomic_json(report_target, portable_data(report))
    metadata = {
        "id": "vue",
        "artifact": {"file": output.name, "format": MODEL_FORMAT, "sha256": file_hash(output),
            "bytes": output.stat().st_size, "parameterCount": sum(value.numel() for value in checkpoint["model"].values()),
            "containsOptimizerState": False, "resumableTrainingCheckpoint": False},
        "selection": {"epoch": checkpoint["epoch"], "metric": "mean per-profile natural real-source validation exact-span macro F1",
                      "score": checkpoint["trainingState"]["bestScore"]},
        "checkpointConfig": checkpoint["modelConfig"],
        "orderedLabels": {"boundary": ["O", "B", "I"], "tokenTypes": checkpoint["schema"]["tokenTypes"],
                          "modifiers": checkpoint["schema"]["modifiers"]},
        "documentKinds": list(KINDS),
        "input": {"encoding": "utf-8", "unit": "byte", "vocabSize": 257, "paddingId": 256, "maxLengthBytes": 512},
        "output": {"offsetEncoding": "utf-16", "interval": "[start,end)", "contract": "../SEMANTICS.md"},
        "inference": {"windowing": "predicted-adaptive-cursor", "decoder": "greedy-mean-logit-with-adjacent-body-coalescing",
                      "modifierThreshold": artifact["trainingConfig"]["modifier_threshold"], "parserRequired": False},
        "scope": "base-vue-markup-and-neural-regions",
        "modelSchema": {"file": "../model-schema.json", "sha256": file_hash(REPOSITORY / "packs/vue/model-schema.json")},
        "publicSchema": {"file": "../schema.json", "sha256": file_hash(REPOSITORY / "packs/vue/schema.json")},
        "dataset": identity,
        "provenance": {"sourceCheckpoint": str(source.resolve()), "sourceCheckpointSha256": source_hash,
                       "training": checkpoint["provenance"], "initialization": checkpoint.get("initialization"),
                       "exporterSha256": file_hash(Path(__file__))},
        "reports": {"test-metrics.json": {"file": "reports/test-metrics.json", "sha256": file_hash(report_target),
            "checkpointHash": source_hash, "split": "test", "inference": "predicted-adaptive-cursor"}},
    }
    atomic_json(output.with_name("model.json"), portable_data(metadata))
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--test-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("packs/vue/model/model.pt"))
    args = parser.parse_args()
    metadata = export_model(args.checkpoint, args.test_report, args.output)
    print(json.dumps(metadata["artifact"], indent=2))


if __name__ == "__main__":
    main()
