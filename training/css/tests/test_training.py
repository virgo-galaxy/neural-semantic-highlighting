from collections import Counter
from dataclasses import asdict
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from packs.css.runtime.local import CssLocalPack, run_stdio
from training.css.checkpoints import (FORMAT, MODEL_FORMAT, capture_rng, load_checkpoint,
    model_from_checkpoint, restore_rng, save_checkpoint, seed_all)
from training.css.losses import compute_loss
from training.css.model import CssSemanticTransformer, ModelConfig, ModelOutput, parameter_count
from training.css.train import TrainingConfig, epoch_batches

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_JSON = json.loads((ROOT / "packs/css/schema.json").read_text())
SCHEMA = {"tokenTypes": [item["id"] for item in SCHEMA_JSON["tokenTypes"]],
          "modifiers": [item["id"] for item in SCHEMA_JSON["tokenModifiers"]]}


def tiny_model():
    return CssSemanticTransformer(ModelConfig(context_bytes=16, width=8, heads=2, layers=1, feed_forward=16),
                                  len(SCHEMA["tokenTypes"]), len(SCHEMA["modifiers"]))


class TrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_baseline_size_and_independent_layer_initialization(self):
        model = CssSemanticTransformer(ModelConfig(), 15, 1)
        self.assertEqual(parameter_count(model), 894227)
        self.assertFalse(torch.equal(model.layers[0].linear1.weight, model.layers[1].linear1.weight))

    def test_checkpoint_resume_replays_dropout_and_optimizer(self):
        seed_all(42)
        model = tiny_model()
        optimizer = torch.optim.AdamW(model.parameters(), lr=.0003)
        ids = torch.tensor([[97, 98, 99]])
        def step(m, opt):
            m.train()
            opt.zero_grad(set_to_none=True)
            m(ids, torch.ones_like(ids, dtype=torch.bool)).boundary.square().mean().backward()
            opt.step()
        step(model, optimizer)
        payload = {"format": FORMAT, "epoch": 1, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
            "modelConfig": model.config.to_dict(), "schema": SCHEMA, "dataset": {},
            "trainingConfig": asdict(TrainingConfig()), "trainingState": {}, "lossWeights": {},
            "rng": capture_rng(torch.device("cpu")), "documentKinds": ["css", "scss", "less"]}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "last.pt"
            save_checkpoint(path, payload)
            step(model, optimizer)
            saved = load_checkpoint(path)
            restored = model_from_checkpoint(saved, torch.device("cpu"))
            resumed_optimizer = torch.optim.AdamW(restored.parameters(), lr=.0003)
            resumed_optimizer.load_state_dict(saved["optimizer"])
            restore_rng(saved["rng"], torch.device("cpu"))
            step(restored, resumed_optimizer)
            for name, value in model.state_dict().items():
                torch.testing.assert_close(value, restored.state_dict()[name], rtol=0, atol=0)

    def test_masks_ignore_continuation_bytes_and_non_begin_modifiers(self):
        output = ModelOutput(torch.randn(1, 4, 3), torch.randn(1, 4, 15), torch.randn(1, 4, 1))
        batch = {"boundary_labels": torch.tensor([[1, -100, 2, 0]]),
                 "token_type_labels": torch.tensor([[0, -100, 0, -100]]),
                 "modifier_targets": torch.tensor([[[1.], [0.], [0.], [0.]]])}
        weights = {"boundary": torch.ones(3), "token_type": torch.ones(15), "modifier": torch.ones(1)}
        first = compute_loss(output, batch, weights)[0]
        output.boundary[0, 1] += 1000
        output.token_type[0, 1] += 1000
        output.token_type[0, 3] += 1000
        output.modifier[0, 1:] += 1000
        torch.testing.assert_close(first, compute_loss(output, batch, weights)[0], rtol=0, atol=0)

    def test_sampler_balances_kinds_and_replays_each_epoch(self):
        refs = [{"documentKind": kind} for kind, count in (("css", 5), ("scss", 2), ("less", 3)) for _ in range(count)]
        split = SimpleNamespace(refs=refs)
        batches = epoch_batches(split, TrainingConfig(batch_size=4), 2)
        self.assertEqual(batches, epoch_batches(split, TrainingConfig(batch_size=4), 2))
        order = [index for batch in batches for index in batch]
        self.assertEqual(set(order), set(range(len(refs))))
        self.assertEqual(Counter(refs[index]["documentKind"] for index in order),
                         {"css": 5, "scss": 5, "less": 5})

    def test_local_runtime_unicode_stdio_and_inference_artifact_cannot_resume(self):
        model = tiny_model()
        with torch.no_grad():
            for parameter in model.parameters():
                parameter.zero_()
            model.boundary_head.bias[1] = 10
            model.token_head.bias[SCHEMA["tokenTypes"].index("string")] = 5
        artifact = {"format": MODEL_FORMAT, "model": model.state_dict(), "modelConfig": model.config.to_dict(),
            "schema": SCHEMA, "dataset": {}, "trainingConfig": {"modifier_threshold": .6}, "epoch": 1,
            "documentKinds": ["css", "scss", "less"]}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.pt"
            save_checkpoint(path, artifact)
            pack = CssLocalPack(checkpoint_path=path, device_name="cpu")
            result = pack.highlight(source="🌌x", document_kind="scss")
            self.assertEqual(result, {"offsetEncoding": "utf-16", "spans": [
                {"start": 0, "end": 2, "tokenType": "string"},
                {"start": 2, "end": 3, "tokenType": "string"}]})
            self.assertEqual(pack.highlight(source="", document_kind="css")["spans"], [])
            requests = "\n".join(json.dumps({"id": index, "source": "x", "documentKind": kind})
                                 for index, kind in ((1, "css"), (2, "unknown"), (3, "less"))) + "\n"
            output = io.StringIO()
            with patch("sys.stdin", io.StringIO(requests)), patch("sys.stdout", output):
                run_stdio(pack)
            responses = list(map(json.loads, output.getvalue().splitlines()))
            self.assertEqual([row["id"] for row in responses], [1, 2, 3])
            self.assertIn("result", responses[0])
            self.assertIn("error", responses[1])
            self.assertIn("result", responses[2])
            with self.assertRaisesRegex(ValueError, "compatible"):
                load_checkpoint(path)


if __name__ == "__main__":
    unittest.main()
