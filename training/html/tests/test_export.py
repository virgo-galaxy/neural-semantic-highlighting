"""Export checks bind inference weights to one held-out runtime report."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest

import torch

from training.html.checkpoints import FORMAT, MODEL_FORMAT, load_checkpoint, save_checkpoint
from training.html.encoding import Schema
from training.html.export_model import export_model
from training.html.model import HtmlSemanticTransformer, ModelConfig
from training.html.prepare import REPOSITORY, file_hash
from training.html.train import TrainingConfig


class ExportTests(unittest.TestCase):
    def test_report_binding_preserves_source_and_exports_inference_only(self):
        schema = Schema.load(REPOSITORY / "packs/html/model-schema.json")
        model = HtmlSemanticTransformer(ModelConfig(width=8, heads=2, layers=1, feed_forward=16),
                                       len(schema.token_types), len(schema.modifiers))
        payload = {"format": FORMAT, "model": model.state_dict(), "modelConfig": model.config.to_dict(),
                   "schema": {"tokenTypes": list(schema.token_types), "modifiers": list(schema.modifiers)},
                   "epoch": 3, "dataset": {"snapshot": "data", "manifestHash": "manifest"},
                   "trainingConfig": asdict(TrainingConfig()), "optimizer": {}, "rng": {}, "lossWeights": {},
                   "documentKinds": ["html"], "trainingState": {"bestScore": .5},
                   "validation": {}, "initialization": {"mode": "test"},
                   "provenance": {"semanticsHash": file_hash(REPOSITORY / "packs/html/SEMANTICS.md")}}
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source, report_path = folder / "best.pt", folder / "test.json"
            save_checkpoint(source, payload)
            original = source.read_bytes()
            report = {"split": "test", "inference": "predicted-adaptive-cursor",
                      "checkpointHash": file_hash(source), "checkpointEpoch": 3,
                      "dataset": payload["dataset"], "smokeCheckpoint": False,
                      "modelConfig": payload["modelConfig"],
                      "scope": "base-markup-and-neural-body-regions", "bodyRegions": {},
                      "documentKinds": {kind: {"documents": 1} for kind in ("html",)}}
            report_path.write_text(json.dumps(report))
            output = folder / "selected/model.pt"
            output.parent.mkdir()
            for name in ("README.md", "BENCHMARKS.md", "KNOWN_ISSUES.md"):
                (output.parent / name).write_text("Reviewed test bundle")
            report["checkpointHash"] = "wrong"
            report_path.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError, "matching held-out"):
                export_model(source, report_path, output)
            self.assertFalse(output.exists())
            report["checkpointHash"] = file_hash(source)
            report_path.write_text(json.dumps(report))
            report_original = report_path.read_bytes()
            metadata = export_model(source, report_path, output)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(report_path.read_bytes(), report_original)
            artifact = torch.load(output, map_location="cpu", weights_only=True)
            self.assertEqual(artifact["format"], MODEL_FORMAT)
            self.assertEqual(artifact["initialization"], payload["initialization"])
            for key in ("optimizer", "rng", "trainingState", "lossWeights"):
                self.assertNotIn(key, artifact)
            for name, value in model.state_dict().items():
                torch.testing.assert_close(artifact["model"][name], value, rtol=0, atol=0)
            self.assertEqual(metadata["artifact"]["sha256"], file_hash(output))
            self.assertEqual(json.loads((output.parent / "reports/test-metrics.json").read_text()), report)
            with self.assertRaisesRegex(ValueError, "compatible HTML checkpoint"):
                load_checkpoint(output)
            with self.assertRaisesRegex(ValueError, "already exists"):
                export_model(source, report_path, output)
            payload["trainingConfig"]["smoke"] = True
            save_checkpoint(source, payload)
            with self.assertRaisesRegex(ValueError, "Smoke checkpoints"):
                export_model(source, report_path, folder / "smoke.pt")


if __name__ == "__main__":
    unittest.main()
