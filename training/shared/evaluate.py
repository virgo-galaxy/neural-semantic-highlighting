"""Independent whole-document pack evaluation with per-kind and per-role metrics."""
from __future__ import annotations

from training.shared.spec import current

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import torch

from training.shared.checkpoints import atomic_json, load_model_artifact, model_from_checkpoint, select_device
from training.shared.metrics import evaluate_adaptive, evaluate_fixed
from training.shared.trainer_data import Snapshot, WindowSplit, sha256_file
from training.shared.provenance import code_hashes
from training.shared.structured import parameters_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--split", choices=["validation", "test"], default="validation")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    parser.add_argument("--inference", choices=["adaptive", "fixed"], default="adaptive")
    parser.add_argument("--output", type=Path)
    parser.add_argument('--cohort-groups', type=Path, help='Frozen JSON name -> natural source-family lists (adaptive only)')
    args = parser.parse_args()
    cohorts = json.loads(args.cohort_groups.read_text()) if args.cohort_groups else None
    if cohorts is not None:
        if (args.inference != 'adaptive' or not isinstance(cohorts, dict) or not cohorts
                or any(not isinstance(v, list) or not v or any(not isinstance(g, str) for g in v) for v in cohorts.values())):
            raise ValueError('Expected nonempty adaptive natural cohort family lists')
        groups = [group for values in cohorts.values() for group in values]
        if len(groups) != len(set(groups)):
            raise ValueError('Evaluation cohorts must have disjoint source families')
    checkpoint_hash = sha256_file(args.checkpoint)
    payload = load_model_artifact(args.checkpoint)
    if sha256_file(args.checkpoint) != checkpoint_hash:
        raise ValueError("Checkpoint changed while loading; evaluate a frozen checkpoint")
    snapshot = Snapshot.open(args.snapshot or Path(payload["dataset"]["path"]))
    if snapshot.identity() != {name: payload["dataset"][name] for name in ("snapshot", "manifestHash")}:
        raise ValueError("Evaluation dataset differs from the checkpoint")
    if payload["schema"] != snapshot.schema:
        raise ValueError("Evaluation schema differs from the checkpoint")
    device = select_device(args.device)
    if device.type == "cpu":
        torch.set_num_threads(min(4, torch.get_num_threads()))
    model = model_from_checkpoint(payload, device)
    split = WindowSplit(snapshot, args.split)
    try:
        options = {'threshold': payload['trainingConfig']['modifier_threshold']}
        if args.inference == 'adaptive': options['cohorts'] = cohorts
        report = (evaluate_adaptive if args.inference == "adaptive" else evaluate_fixed)(model, split, device, **options)
        report.update(checkpointHash=checkpoint_hash, checkpointEpoch=payload["epoch"],
            decoderPolicy=current().decoder(),
            smokeCheckpoint=bool(payload["trainingConfig"].get("smoke")), dataset=snapshot.identity(),
            modelConfig=payload["modelConfig"], device=device.type, torchVersion=str(torch.__version__), codeHashes=code_hashes())
        if payload.get('structuredDecoder') is not None:
            report['structuredDecoderHash'] = parameters_hash(payload['structuredDecoder'])
        if args.cohort_groups:
            report['cohortGroupsHash'] = sha256_file(args.cohort_groups)
    finally:
        split.close()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    path = args.output or args.checkpoint.parent / f"{args.split}-{args.inference}-{stamp}.json"
    atomic_json(path, report)
    for kind, metrics in report["documentKinds"].items():
        print(kind, "F1", round(metrics["exactSpan"]["f1"], 4), "macro",
              round(metrics["exactSpanMacroF1"], 4), "documents", metrics["documents"])
    print("Report:", path)


if __name__ == "__main__":
    main()
