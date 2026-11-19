import unittest
import torch

from training.shared.average import assert_holdouts, blend


class AveragingTests(unittest.TestCase):
    def test_convex_weights_preserve_tensor_contract(self):
        value=blend([{'a':torch.tensor([1.,3.])},{'a':torch.tensor([5.,7.])}],[.75,.25])
        torch.testing.assert_close(value['a'],torch.tensor([2.,4.]))
        for weights in [[1.,1.],[-1.,2.],[float('nan'),.5]]:
            with self.assertRaises(ValueError):blend([{'a':torch.tensor([1.])}]*2,weights)
        with self.assertRaises(ValueError):blend([{'a':torch.zeros(1)},{'a':torch.zeros(2)}],[.5,.5])

    def test_parent_holdout_leakage_is_rejected(self):
        assert_holdouts({'train'},{'validation','test'})
        with self.assertRaises(ValueError):assert_holdouts({'test'},{'validation','test'})
