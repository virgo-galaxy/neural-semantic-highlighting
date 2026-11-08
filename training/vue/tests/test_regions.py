import json
from pathlib import Path
import tempfile
import unittest

import torch

from training.vue.checkpoints import save_checkpoint
from training.vue.encoding import Schema
from training.vue.inference import decode
from training.vue.initialization import initialize_from_checkpoint
from training.vue.metrics import RegionMetrics
from training.vue.model import VueSemanticTransformer, ModelConfig, ModelOutput
from training.vue.prepare import REPOSITORY


class RegionTests(unittest.TestCase):
    def test_region_coverage_does_not_hide_boundary_or_language_errors(self):
        gold = {"spans": [{"start": 10, "end": 20, "tokenType": "embedded-javascript"}]}
        pred = {"spans": [{"start": 12, "end": 19, "tokenType": "embedded-javascript"}]}
        metrics = RegionMetrics()
        metrics.add(gold, pred)
        report = metrics.report()
        self.assertEqual(report["exactRegions"]["exactSpan"]["f1"], 0)
        coverage = report["utf16CoverageByRole"]["embedded-javascript"]
        self.assertEqual((coverage["tp"], coverage["fp"], coverage["fn"]), (7, 0, 3))
        pred["spans"][0]["tokenType"] = "embedded-css"
        metrics = RegionMetrics()
        metrics.add(gold, pred)
        self.assertEqual(metrics.report()["utf16CoverageByRole"]["embedded-javascript"]["tp"], 0)

    def test_decoder_coalesces_neural_body_roles_without_source_parsing(self):
        schema = {"tokenTypes": ["tag", "embedded-css"], "modifiers": ["closing"]}
        output = ModelOutput(torch.tensor([[0., 10., 0.]] * 3), torch.tensor([[0., 10.]] * 3), torch.full((3, 1), 20.))
        self.assertEqual(decode("abc", output, schema)["spans"], [{"start": 0, "end": 3, "tokenType": "embedded-css"}])

    def test_transfer_matches_semantic_names_and_keeps_new_roles_and_closing_head(self):
        schema = Schema.load(REPOSITORY / "packs/vue/model-schema.json")
        cfg = ModelConfig(context_bytes=16, width=8, heads=2, layers=1, feed_forward=16)
        target = VueSemanticTransformer(ModelConfig(**{**cfg.to_dict(), "local_kernel": 3}),
                                         len(schema.token_types), len(schema.modifiers))
        source = VueSemanticTransformer(cfg, 3, 1)
        names = ["attribute", "string", "tag"]
        with torch.no_grad():
            for i in range(3): source.token_head.weight[i].fill_(10 + i)
        text_before = target.token_head.weight[schema.token_types.index("text")].clone()
        closing_before = target.modifier_head.weight.clone()
        payload = {"format": "nsh-css-checkpoint-v1", "model": source.state_dict(), "modelConfig": cfg.to_dict(),
                   "schema": {"tokenTypes": names, "modifiers": ["declaration"]}, "epoch": 8,
                   "dataset": {}, "trainingConfig": {"smoke": False}, "optimizer": {}, "rng": {}, "trainingState": {}}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "best.pt"
            save_checkpoint(path, payload)
            original = path.read_bytes()
            lineage = initialize_from_checkpoint(target, path)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(lineage["mode"], "css-weights-only-transfer")
            self.assertEqual(lineage["newTensors"], ["local_context.bias", "local_context.weight"])
            self.assertFalse(bool(target.local_context.weight.any()))
            for i, name in enumerate(names):
                torch.testing.assert_close(target.token_head.weight[schema.token_types.index(name)], source.token_head.weight[i])
            torch.testing.assert_close(target.token_head.weight[schema.token_types.index("text")], text_before)
            torch.testing.assert_close(target.modifier_head.weight, closing_before)
            torch.testing.assert_close(target.layers[0].linear1.weight, source.layers[0].linear1.weight)
            payload["format"] = "nsh-css-model-v1"
            save_checkpoint(path, payload)
            with self.assertRaisesRegex(ValueError, "full, non-smoke"):
                initialize_from_checkpoint(target, path)


if __name__ == "__main__": unittest.main()
