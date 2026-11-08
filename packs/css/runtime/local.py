"""Pure-neural CSS-family inference; no CSS/Sass/Less parser or compiler at runtime."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import torch

from training.css.checkpoints import load_model_artifact, model_from_checkpoint, select_device
from training.css.inference import decode, document_logits

PACK_DIRECTORY = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PACK_DIRECTORY / "model/model.pt"


class CssLocalPack:
    def __init__(self, *, checkpoint_path: Path = DEFAULT_MODEL_PATH, device_name: str = "auto"):
        self.device = select_device(device_name)
        if self.device.type == "cpu":
            torch.set_num_threads(min(4, torch.get_num_threads()))
        if not checkpoint_path.is_file():
            raise ValueError("No selected CSS model at this path; use --checkpoint with a CSS training candidate")
        self.manifest = json.loads((PACK_DIRECTORY / "manifest.json").read_text())
        self.document_kinds = frozenset(item["id"] for item in self.manifest["documentKinds"])
        self.checkpoint = load_model_artifact(checkpoint_path)
        if set(self.checkpoint.get("documentKinds", [])) != self.document_kinds:
            raise ValueError("CSS artifact/document-kind mismatch")
        schema = json.loads((PACK_DIRECTORY / "schema.json").read_text())
        expected = {"tokenTypes": [item["id"] for item in schema["tokenTypes"]],
                    "modifiers": [item["id"] for item in schema["tokenModifiers"]]}
        if self.checkpoint["schema"] != expected:
            raise ValueError("CSS artifact/schema mismatch")
        self.model = model_from_checkpoint(self.checkpoint, self.device)
        self.model.eval()

    def highlight(self, *, source: str, document_kind: str) -> dict:
        if document_kind not in self.document_kinds:
            raise ValueError("Unsupported CSS document kind: " + document_kind)
        return decode(source, document_logits(self.model, source, self.device), self.checkpoint["schema"],
                      threshold=self.checkpoint["trainingConfig"]["modifier_threshold"])


def run_stdio(pack: CssLocalPack):
    for line in sys.stdin:
        if not line.strip():
            continue
        request_id = None
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("Request must be a JSON object")
            request_id = request.get("id")
            if not isinstance(request.get("source"), str) or not isinstance(request.get("documentKind"), str):
                raise ValueError("Request requires source and documentKind strings")
            response = {"id": request_id, "result": pack.highlight(source=request["source"],
                document_kind=request["documentKind"])}
        except Exception as error:
            response = {"id": request_id, "error": {"message": str(error)}}
        print(json.dumps(response, ensure_ascii=False, separators=(",", ":")), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--stdio", action="store_true")
    modes.add_argument("--text")
    modes.add_argument("--file", type=Path)
    parser.add_argument("--document-kind", choices=["css", "scss", "less"], default="css")
    args = parser.parse_args()
    pack = CssLocalPack(checkpoint_path=args.checkpoint.expanduser().resolve(), device_name=args.device)
    if args.stdio:
        run_stdio(pack)
    else:
        source = args.file.read_bytes().decode("utf-8") if args.file else args.text
        print(json.dumps(pack.highlight(source=source, document_kind=args.document_kind), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
