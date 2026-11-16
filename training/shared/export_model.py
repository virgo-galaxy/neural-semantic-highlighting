"""Promote a reviewed pack checkpoint with a matching independent adaptive test report."""
from __future__ import annotations

from training.shared.spec import current

import argparse
import json
from pathlib import Path

import torch

from training.shared.checkpoints import atomic_json, load_checkpoint, save_checkpoint
from training.shared.prepare import REPOSITORY, file_hash
from training.shared.structured import parameters_hash



def export_model(source: Path, test_report: Path, output: Path) -> dict:
    source_hash = file_hash(source)
    checkpoint = load_checkpoint(source)
    current().verify_config(checkpoint.get('provenance',{}))
    if file_hash(source) != source_hash:
        raise ValueError("Checkpoint changed while loading; export a frozen checkpoint")
    if checkpoint["trainingConfig"].get("smoke"):
        raise ValueError("Smoke checkpoints cannot become a selected pack model")
    if checkpoint["modelConfig"]["context_bytes"] != 512 or checkpoint.get("documentKinds") != list(current().document_kinds):
        raise ValueError("Expected the pack baseline configuration")
    report = json.loads(test_report.read_text())
    if report.get('structuredDecoderHash') != parameters_hash(checkpoint.get('structuredDecoder')):
        raise ValueError('Test report must use the frozen structured decoder')
    identity = {key: checkpoint["dataset"][key] for key in ("snapshot", "manifestHash")}
    if (report.get("split") != "test" or report.get("inference") != "predicted-adaptive-cursor"
            or report.get("checkpointHash") != source_hash or report.get("checkpointEpoch") != checkpoint["epoch"]
            or report.get("dataset") != identity or report.get("smokeCheckpoint") is not False
            or report.get("modelConfig") != checkpoint["modelConfig"]):
        raise ValueError("A matching held-out adaptive test report is required")
    if any(report.get("documentKinds", {}).get(kind, {}).get("documents", 0) < 1 for kind in current().document_kinds):
        raise ValueError("Every pack document kind needs independent test evidence")
    if any(report.get("profiles", {}).get(profile, {}).get("natural", {}).get("documents", 0) < 1
           for profile in current().profiles):
        raise ValueError("Every pack coverage profile needs real-source independent test evidence")
    if report.get("scope") != current().scope:
        raise ValueError("Explicit base-model scope and body-region evidence are required")
    if checkpoint["provenance"]["semanticsHash"] != file_hash(current().semantics_path):
        raise ValueError("Checkpoint semantic contract differs from the current pack")
    if output.resolve() in {source.resolve(), test_report.resolve()}:
        raise ValueError("Export must preserve the original checkpoint and report")
    if output.exists():
        raise ValueError("Export target already exists; preserve the previous selected model bundle")
    for document in ("README.md", "BENCHMARKS.md", "KNOWN_ISSUES.md"):
        if not (output.parent / document).is_file():
            raise ValueError("Prepare the reviewed model documentation before export: " + document)
    artifact = {"format": current().model_format, "model": checkpoint["model"], "modelConfig": checkpoint["modelConfig"],
        "schema": checkpoint["schema"], "dataset": checkpoint["dataset"], "epoch": checkpoint["epoch"],
        "documentKinds": list(current().document_kinds),
        "trainingConfig": {"modifier_threshold": checkpoint["trainingConfig"]["modifier_threshold"]},
        "validation": checkpoint["validation"], "provenance": checkpoint["provenance"],
        "initialization": checkpoint.get("initialization")}
    if checkpoint.get('structuredDecoder') is not None:
        from training.shared.structured import validate
        validate(checkpoint['structuredDecoder'], checkpoint['schema'])
        artifact['structuredDecoder'] = checkpoint['structuredDecoder']
        artifact['decoderCalibration'] = checkpoint['decoderCalibration']
        calibration_path = Path(artifact['decoderCalibration']['validationReport'])
        if (artifact['decoderCalibration'].get('primaryTestUsed') is not False
                or file_hash(calibration_path) != artifact['decoderCalibration']['validationReportHash']):
            raise ValueError('Calibrated export requires intact validation-only selection evidence')
        calibration = json.loads(calibration_path.read_text())
        if calibration.get('primaryTestUsed') is not False:
            raise ValueError('Decoder calibration must not use independent test predictions')
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
        atomic_json(report_target, report)
    metadata = {
        "id": current().id,
        "artifact": {"file": output.name, "format": current().model_format, "sha256": file_hash(output),
            "bytes": output.stat().st_size, "parameterCount": sum(value.numel() for value in checkpoint["model"].values()),
            "containsOptimizerState": False, "resumableTrainingCheckpoint": False},
        "selection": {"epoch": checkpoint["epoch"], "metric": "mean per-profile natural real-source validation exact-span macro F1",
                      "score": checkpoint["trainingState"]["bestScore"]},
        "checkpointConfig": checkpoint["modelConfig"],
        "orderedLabels": {"boundary": ["O", "B", "I"], "tokenTypes": checkpoint["schema"]["tokenTypes"],
                          "modifiers": checkpoint["schema"]["modifiers"]},
        "documentKinds": list(current().document_kinds),
        "input": {"encoding": "utf-8", "unit": "byte", "vocabSize": 257, "paddingId": 256, "maxLengthBytes": 512},
        "output": {"offsetEncoding": "utf-16", "interval": "[start,end)", "contract": "../SEMANTICS.md"},
        "inference": {"windowing": "predicted-adaptive-cursor", "decoder": "joint-bio-viterbi" if artifact.get('structuredDecoder') else "greedy-mean-logit",
                      "packPolicy": current().decoder(),
                      "modifierThreshold": artifact["trainingConfig"]["modifier_threshold"], "parserRequired": False},
        "scope": current().scope,
        "modelSchema": {"file": "../schema.json", "sha256": file_hash(current().schema_path)},
        "publicSchema": {"file": "../schema.json", "sha256": file_hash(current().schema_path)},
        "dataset": identity,
        "provenance": {"sourceCheckpoint": str(source.resolve()), "sourceCheckpointSha256": source_hash,
                       "training": checkpoint["provenance"], "initialization": checkpoint.get("initialization"),
                       "exporterSha256": file_hash(Path(__file__))},
        "reports": {"test-metrics.json": {"file": "reports/test-metrics.json", "sha256": file_hash(report_target),
            "checkpointHash": source_hash, "split": "test", "inference": "predicted-adaptive-cursor"}},
    }
    if artifact.get('decoderCalibration'):
        metadata['provenance']['decoderCalibration'] = artifact['decoderCalibration']
        metadata['selection'] = dict(epoch=checkpoint['epoch'],
            metric=calibration['selection'], score=calibration['selected']['selectionScore'],
            validationReportSha256=file_hash(calibration_path),
            trainingBestEpoch=checkpoint['trainingState']['bestEpoch'],
            trainingBestFixedMacroF1=checkpoint['trainingState']['bestScore'])
    atomic_json(output.with_name("model.json"), metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--test-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=current().directory / "model/model.pt")
    args = parser.parse_args()
    metadata = export_model(args.checkpoint, args.test_report, args.output)
    print(json.dumps(metadata["artifact"], indent=2))


if __name__ == "__main__":
    main()
