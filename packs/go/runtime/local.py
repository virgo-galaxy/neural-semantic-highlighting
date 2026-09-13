"""Run the trained Go semantic model locally without the Go toolchain."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import torch

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
TRAINING_DIRECTORY = REPOSITORY_ROOT / "training" / "go"
if str(TRAINING_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TRAINING_DIRECTORY))

from checkpoints import load_model_artifact, model_from_checkpoint, select_device  # noqa: E402
from inference import decode, document_logits  # noqa: E402

PACK_DIRECTORY = REPOSITORY_ROOT / "packs" / "go"
DEFAULT_MODEL_PATH = PACK_DIRECTORY / "model" / "model.pt"
DEFAULT_MANIFEST_PATH = PACK_DIRECTORY / "manifest.json"


class GoLocalPack:
    """Keep one Go model loaded and answer HighlightRequest messages."""

    def __init__(
        self,
        *,
        checkpoint_path: Path = DEFAULT_MODEL_PATH,
        manifest_path: Path = DEFAULT_MANIFEST_PATH,
        device_name: str = "auto",
    ) -> None:
        self.device = select_device(device_name)
        if self.device.type == "cpu":
            torch.set_num_threads(min(8, torch.get_num_threads()))

        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.document_kinds = frozenset(
            item["id"] for item in self.manifest["documentKinds"]
        )
        self.checkpoint = load_model_artifact(checkpoint_path)
        self.model = model_from_checkpoint(self.checkpoint, self.device)
        self.model.eval()
        self.modifier_threshold = float(
            self.checkpoint["trainingConfig"]["modifier_threshold"]
        )

    def highlight(self, *, source: str, document_kind: str) -> dict[str, Any]:
        if document_kind not in self.document_kinds:
            raise ValueError(f'Unsupported document kind "{document_kind}".')

        logits = document_logits(self.model, source, self.device, adaptive=True)
        return decode(
            source,
            logits,
            self.checkpoint["schema"],
            threshold=self.modifier_threshold,
        )


def run_stdio(pack: GoLocalPack) -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        request_id: Any = None

        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("Request must be a JSON object.")

            request_id = request.get("id")
            source = request.get("source")
            document_kind = request.get("documentKind")

            if not isinstance(source, str):
                raise ValueError('Request field "source" must be a string.')
            if not isinstance(document_kind, str):
                raise ValueError('Request field "documentKind" must be a string.')

            response = {
                "id": request_id,
                "result": pack.highlight(source=source, document_kind=document_kind),
            }
        except Exception as error:
            response = {
                "id": request_id,
                "error": {"message": str(error)},
            }

        print(json.dumps(response, ensure_ascii=False, separators=(",", ":")), flush=True)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Keep the model loaded and exchange JSONL messages over stdin/stdout.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    if not args.stdio:
        raise SystemExit("This runtime currently requires --stdio.")

    pack = GoLocalPack(
        checkpoint_path=args.checkpoint.expanduser().resolve(),
        device_name=args.device,
    )
    run_stdio(pack)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
