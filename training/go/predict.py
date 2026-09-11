"""Predict Go semantic spans from a local checkpoint, without any Go toolchain."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import torch

from checkpoints import atomic_json, load_checkpoint, model_from_checkpoint, select_device
from inference import decode, document_logits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--source", type=Path, help="UTF-8 Go source file; omitted means read stdin")
    parser.add_argument("--output", type=Path, help="Write HighlightResult here instead of stdout")
    parser.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    args = parser.parse_args()
    try:
        checkpoint = load_checkpoint(args.checkpoint)
        device = select_device(args.device)
        if device.type == "cpu":
            torch.set_num_threads(min(8, torch.get_num_threads()))
        # Read bytes to preserve CRLF exactly. read_text() would normalize it.
        source = (args.source.read_bytes() if args.source else sys.stdin.buffer.read()).decode("utf-8")
        model = model_from_checkpoint(checkpoint, device)
        output = document_logits(model, source, device)
        result = decode(source, output, checkpoint["schema"], threshold=checkpoint["trainingConfig"]["modifier_threshold"])
        if args.output:
            atomic_json(args.output, result)
        else:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"Go prediction failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
