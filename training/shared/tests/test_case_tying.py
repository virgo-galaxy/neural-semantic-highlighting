from types import SimpleNamespace
import unittest
import torch

from training.shared.train import tie_ascii_case


class CaseTyingTests(unittest.TestCase):
    def test_preserves_lowercase_and_constraint_after_adam_update(self):
        embedding=torch.nn.Embedding(257,8)
        model=SimpleNamespace(byte_embedding=embedding)
        old=embedding.weight.detach().clone()
        tie_ascii_case(model)
        torch.testing.assert_close(embedding.weight[97:123],old[97:123],rtol=0,atol=0)
        torch.testing.assert_close(embedding.weight[65:91],embedding.weight[97:123],rtol=0,atol=0)
        optimizer=torch.optim.AdamW(embedding.parameters(),lr=.001)
        embedding(torch.tensor([65,65,66,97,99])).square().mean().backward()
        tie_ascii_case(model,gradients=True);optimizer.step()
        torch.testing.assert_close(embedding.weight[65:91],embedding.weight[97:123],rtol=0,atol=0)
        torch.testing.assert_close(embedding.weight[256],old[256]*(1-.001*.01),rtol=1e-6,atol=1e-6)
