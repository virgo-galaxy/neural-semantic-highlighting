from pathlib import Path
import importlib.util
import unittest
import torch

spec=importlib.util.spec_from_file_location('nsh_ts_losses',Path(__file__).resolve().parents[2]/'typescript/losses.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class TypeScriptLossTests(unittest.TestCase):
    def test_uniform_position_weights_match_existing_weighted_loss(self):
        logits=torch.tensor([[[1.,2.,3.],[3.,1.,2.],[4.,2.,1.]]],requires_grad=True)
        targets=torch.tensor([[2,0,-100]])
        criterion=torch.nn.CrossEntropyLoss(weight=torch.tensor([.5,2.,4.]),ignore_index=-100)
        expected=criterion(logits.reshape(-1,3),targets.reshape(-1))
        actual=module.weighted_token_loss(logits,targets,criterion,torch.ones_like(targets,dtype=torch.float32))
        torch.testing.assert_close(actual,expected)
        actual.backward();torch.testing.assert_close(logits.grad[0,2],torch.zeros(3))
