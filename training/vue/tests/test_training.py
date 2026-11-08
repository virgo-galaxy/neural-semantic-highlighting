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

from packs.vue.runtime.local import VueLocalPack, run_stdio
from training.vue.checkpoints import (FORMAT, MODEL_FORMAT, capture_rng, load_checkpoint,
    model_from_checkpoint, restore_rng, save_checkpoint, seed_all)
from training.vue.losses import compute_loss
from training.vue.initialization import initialize_from_checkpoint
from training.vue.model import VueSemanticTransformer, ModelConfig, ModelOutput, parameter_count
from training.vue.train import TrainingConfig, epoch_batches

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_JSON = json.loads((ROOT / "packs/vue/model-schema.json").read_text())
SCHEMA = {"tokenTypes": [item["id"] for item in SCHEMA_JSON["tokenTypes"]],
          "modifiers": [item["id"] for item in SCHEMA_JSON["tokenModifiers"]]}


def tiny_model():
    return VueSemanticTransformer(ModelConfig(context_bytes=16, width=8, heads=2, layers=1, feed_forward=16),
                                  len(SCHEMA["tokenTypes"]), len(SCHEMA["modifiers"]))


class TrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_baseline_size_and_independent_layer_initialization(self):
        model = VueSemanticTransformer(ModelConfig(), 17, 1)
        self.assertEqual(parameter_count(model), 894485)
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
            "rng": capture_rng(torch.device("cpu")), "documentKinds": ["vue"]}
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

    def test_local_context_starts_as_identity_and_survives_checkpoint_reload(self):
        plain = tiny_model().eval()
        config = {**plain.config.to_dict(), "local_kernel": 3}
        local = VueSemanticTransformer(ModelConfig(**config), 17, 1).eval()
        local.load_state_dict(plain.state_dict(), strict=False)
        ids = torch.tensor([[60, 98, 62]])
        mask = torch.ones_like(ids, dtype=torch.bool)
        torch.testing.assert_close(plain(ids, mask).boundary, local(ids, mask).boundary, rtol=0, atol=0)
        with torch.no_grad(): local.local_context.weight.fill_(.1)
        payload = {"modelConfig": config, "schema": SCHEMA, "model": local.state_dict()}
        restored = model_from_checkpoint(payload, torch.device("cpu")).eval()
        torch.testing.assert_close(local(ids, mask).boundary, restored(ids, mask).boundary, rtol=0, atol=0)

    def test_masks_ignore_continuation_bytes_and_non_begin_modifiers(self):
        output = ModelOutput(torch.randn(1, 4, 3), torch.randn(1, 4, 17), torch.randn(1, 4, 1))
        batch = {"boundary_labels": torch.tensor([[1, -100, 2, 0]]),
                 "token_type_labels": torch.tensor([[0, -100, 0, -100]]),
                 "modifier_targets": torch.tensor([[[1.], [0.], [0.], [0.]]])}
        weights = {"boundary": torch.ones(3), "token_type": torch.ones(17), "modifier": torch.ones(1)}
        first = compute_loss(output, batch, weights)[0]
        output.boundary[0, 1] += 1000
        output.token_type[0, 1] += 1000
        output.token_type[0, 3] += 1000
        output.modifier[0, 1:] += 1000
        torch.testing.assert_close(first, compute_loss(output, batch, weights)[0], rtol=0, atol=0)

    def test_sampler_shuffles_each_window_once(self):
        split = SimpleNamespace(refs=[{"documentKind": "vue"} for _ in range(13)])
        first = epoch_batches(split, TrainingConfig(batch_size=4), 2)
        self.assertEqual(first, epoch_batches(split, TrainingConfig(batch_size=4), 2))
        self.assertEqual(sorted(i for batch in first for i in batch), list(range(13)))

    def test_curriculum_is_bounded_and_rotates_without_replacing_natural_windows(self):
        refs = [{"documentKind": "vue", "stream": "natural"} for _ in range(13)]
        refs += [{"documentKind": "vue", "stream": "focus"} for _ in range(50)]
        split = SimpleNamespace(refs=refs)
        config = TrainingConfig(batch_size=8, focus_batch_size=4)
        first = epoch_batches(split, config, 1)
        self.assertEqual(first, epoch_batches(split, config, 1))
        self.assertEqual(sorted(i for b in first for i in b if i < 13), list(range(13)))
        focus_first = {i for b in first for i in b if i >= 13}
        focus_second = {i for b in epoch_batches(split, config, 2) for i in b if i >= 13}
        self.assertEqual(len(focus_first), 8)
        self.assertFalse(focus_first & focus_second)

    def test_local_runtime_unicode_stdio_and_inference_artifact_cannot_resume(self):
        model = tiny_model()
        with torch.no_grad():
            for parameter in model.parameters():
                parameter.zero_()
            model.boundary_head.bias[1] = 10
            model.token_head.bias[SCHEMA["tokenTypes"].index("text")] = 5
        artifact = {"format": MODEL_FORMAT, "model": model.state_dict(), "modelConfig": model.config.to_dict(),
            "schema": SCHEMA, "dataset": {}, "trainingConfig": {"modifier_threshold": .6}, "epoch": 1,
            "documentKinds": ["vue"]}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.pt"
            save_checkpoint(path, artifact)
            pack = VueLocalPack(checkpoint_path=path, device_name="cpu")
            result = pack.highlight(source="🌌x", document_kind="vue")
            self.assertEqual(result, {"offsetEncoding": "utf-16", "spans": [
                {"start": 0, "end": 2, "tokenType": "text"},
                {"start": 2, "end": 3, "tokenType": "text"}]})
            self.assertEqual(pack.highlight(source="", document_kind="vue")["spans"], [])
            requests = "\n".join(json.dumps({"id": index, "source": "x", "documentKind": kind})
                                 for index, kind in ((1, "vue"), (2, "unknown"), (3, "vue"))) + "\n"
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
