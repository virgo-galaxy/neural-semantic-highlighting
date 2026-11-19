import unittest

import torch

from packs.typescript.runtime.local import SemanticTransformer
from training.browser.model import BrowserTransformer


class TypeScriptLocalTests(unittest.TestCase):
    def model(self, kernel):
        return SemanticTransformer(vocab_size=257, number_of_boundary_classes=3,
            number_of_token_types=4, number_of_modifiers=2, max_length=64,
            embedding_dimension=16, number_of_heads=4, number_of_layers=1,
            feed_forward_dimension=32, local_kernel=kernel).eval()

    def test_zero_residual_preserves_historical_logits(self):
        original=self.model(1);expanded=self.model(5)
        state=expanded.load_state_dict(original.state_dict(),strict=False)
        self.assertEqual(set(state.missing_keys),{'local_context.weight','local_context.bias'})
        self.assertEqual(state.unexpected_keys,[])
        ids=torch.tensor([[32,240,159,140,140,10,59]])
        with torch.inference_mode():
            a=original(ids,torch.ones_like(ids,dtype=torch.bool))
            b=expanded(ids,torch.ones_like(ids,dtype=torch.bool))
        for name in ['boundary_logits','token_type_logits','modifier_logits']:
            torch.testing.assert_close(getattr(a,name),getattr(b,name),rtol=0,atol=0)

    def test_browser_graph_includes_learned_local_context(self):
        model=self.model(5)
        with torch.no_grad():model.local_context.weight.fill_(.01)
        ids=torch.tensor([[65,47,66,59,10]])
        with torch.inference_mode():
            native=model(ids,torch.ones_like(ids,dtype=torch.bool));browser=BrowserTransformer(model)(ids)
        for expected,actual in zip([native.boundary_logits,native.token_type_logits,native.modifier_logits],browser):
            torch.testing.assert_close(expected,actual,rtol=1e-5,atol=1e-5)
