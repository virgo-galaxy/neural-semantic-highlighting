"""Explicit held-out Go evaluation; never called on test data by the trainer."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

import torch

from checkpoints import atomic_json, load_checkpoint, model_from_checkpoint, select_device
from metrics import evaluate_adaptive, evaluate_fixed
from quality import TARGET_F1, targeted_gate_summary, targeted_scores
from trainer_data import Snapshot, WindowSplit, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--split", choices=["validation", "test"], default="validation")
    parser.add_argument("--inference", choices=["adaptive", "fixed"], default="adaptive")
    parser.add_argument("--batch-size", type=int, default=32, help="Used only by fixed-window evaluation")
    parser.add_argument("--device", choices=["auto", "mps", "cuda", "cpu"], default="auto")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    split = None
    try:
        if args.batch_size < 1:
            raise ValueError("Batch size must be positive")
        checkpoint = load_checkpoint(args.checkpoint)
        if checkpoint["trainingConfig"]["smoke"] and args.split == "test":
            raise ValueError("Do not spend the held-out test set on a smoke checkpoint")
        snapshot = Snapshot.open(args.snapshot or Path(checkpoint["snapshotPath"]))
        if snapshot.identity() != checkpoint["dataset"] or snapshot.schema != checkpoint["schema"]:
            raise ValueError("Evaluation snapshot or schema does not match checkpoint")
        device = select_device(args.device)
        if device.type == "cpu":
            torch.set_num_threads(min(8, torch.get_num_threads()))
        split = WindowSplit(snapshot, args.split)
        model = model_from_checkpoint(checkpoint, device)
        threshold = checkpoint["trainingConfig"]["modifier_threshold"]
        if args.inference == "adaptive":
            report = evaluate_adaptive(model, split, device, threshold=threshold)
        else:
            report = evaluate_fixed(model, split, device, threshold=threshold, batch_size=args.batch_size)
        report["targetedRoleGate"] = targeted_gate_summary(report)
        report.update(dataset=snapshot.identity(), checkpointHash=sha256_file(args.checkpoint),
                      checkpointEpoch=checkpoint["epoch"], smokeCheckpoint=checkpoint["trainingConfig"]["smoke"])
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        output = args.output or args.checkpoint.parent / f"{args.split}-{args.inference}-{stamp}.json"
        atomic_json(output, report)
        for kind, values in report["streams"].items():
            print(f"{kind}: {values['documents']} documents, exact F1={values['exactSpan']['f1']:.4f}, "
                  f"macro={values['exactSpanMacroF1']:.4f}")
        print(f"Targeted role scoreboard (gate >= {TARGET_F1:.2f})")
        for row in targeted_scores(report):
            value = 'n/a' if row['f1'] is None else f"{row['f1']:.4f}"
            status = 'PASS' if row['passed'] else 'FAIL'
            print(f"  {row['feature']} / {row['role']}: {value} (support {row['support']}) {status}")
        print(f"Report: {output}")
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"Go evaluation failed: {error}", file=sys.stderr)
        return 1
    finally:
        if split is not None:
            split.close()


if __name__ == "__main__":
    raise SystemExit(main())
