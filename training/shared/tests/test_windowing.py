from pathlib import Path
from types import SimpleNamespace
import json
import unittest
import torch
from training.shared.inference import document_logits, character_map
from training.shared.model import ModelOutput
from training.shared.windowing import validate


class ToyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.config = SimpleNamespace(context_bytes=512)
        self.token_head = SimpleNamespace(out_features=2)
        self.modifier_head = SimpleNamespace(out_features=1)

    def forward(self, ids, mask):
        position = torch.arange(ids.shape[1]).unsqueeze(0)
        boundary = torch.stack([((ids+position)%11==0).float()*2,
            ((ids+position)%7==0).float()*3, torch.ones_like(ids).float()], -1)
        role = torch.stack([(ids%13).float()*.1, (position%17).float().expand_as(ids)*.2], -1)
        modifier = ((ids%5).float()*.25).unsqueeze(-1)
        return ModelOutput(boundary, role, modifier)


def fixture():
    source = 'echo α🌌 value /path/file --flag\r\n' * 24
    starts, _ = character_map(source)
    cases = []
    for stride, weight in [(256, 0), (128, .5)]:
        model = ToyModel().eval()
        model.inference_windowing = dict(format='nsh-overlap-logits-v1', strideBytes=stride, edgeWeightCap=128, adaptiveWeight=weight)
        logits = document_logits(model, source, torch.device('cpu'))
        cases.append(dict(policy=model.inference_windowing,
            expected=[v[starts[:-1]].reshape(-1).tolist() for v in [logits.boundary,logits.token_type,logits.modifier]]))
    return dict(source=source, cases=cases)


class WindowingTests(unittest.TestCase):
    def test_invalid_configuration_is_rejected(self):
        for value in [None, {}, dict(format='nsh-overlap-logits-v1',strideBytes=0,edgeWeightCap=128,adaptiveWeight=0),
                      dict(format='nsh-overlap-logits-v1',strideBytes=128,edgeWeightCap=128,adaptiveWeight=float('nan'))]:
            with self.assertRaises(ValueError):validate(value)

    def test_short_original_utf8_input_retains_existing_logits(self):
        model=ToyModel().eval();source='α🌌\r\necho x'
        original=document_logits(model,source,torch.device('cpu'))
        model.inference_windowing=dict(format='nsh-overlap-logits-v1',strideBytes=128,edgeWeightCap=128,adaptiveWeight=.5)
        actual=document_logits(model,source,torch.device('cpu'))
        for a,b in zip([original.boundary,original.token_type,original.modifier],[actual.boundary,actual.token_type,actual.modifier]):
            torch.testing.assert_close(a,b,rtol=0,atol=0)
        empty=document_logits(model,'',torch.device('cpu'))
        self.assertEqual(empty.boundary.shape,(0,3))

    def test_long_policy_inference_disables_dropout_before_its_first_window(self):
        class DropoutToy(ToyModel):
            def forward(self, ids, mask):
                output=super().forward(ids,mask)
                output.token_type=torch.nn.functional.dropout(output.token_type,p=.5,training=self.training)
                return output
        model=DropoutToy()
        model.inference_windowing=dict(format='nsh-overlap-logits-v1',strideBytes=128,edgeWeightCap=128,adaptiveWeight=.5)
        actual=document_logits(model,'alpha🌌 '*100,torch.device('cpu'))
        expected=document_logits(model,'alpha🌌 '*100,torch.device('cpu'))
        self.assertFalse(model.training)
        torch.testing.assert_close(actual.token_type,expected.token_type,rtol=0,atol=0)

    def test_validation_window_cache_preserves_logits_and_reuses_neural_calls(self):
        from training.shared.windowing import overlap_logits
        class CountingToy(ToyModel):
            calls=0
            def forward(self,ids,mask):
                self.calls+=1
                return super().forward(ids,mask)
        model=CountingToy().eval();source='original α🌌 '*150;cache={}
        first=dict(format='nsh-overlap-logits-v1',strideBytes=256,edgeWeightCap=128,adaptiveWeight=0)
        second=dict(first,strideBytes=128)
        overlap_logits(model,source,torch.device('cpu'),first,window_cache=cache)
        previous=model.calls
        cached=overlap_logits(model,source,torch.device('cpu'),second,window_cache=cache)
        reused=model.calls-previous
        previous=model.calls
        plain=overlap_logits(model,source,torch.device('cpu'),second)
        self.assertLess(reused,model.calls-previous)
        for a,b in zip([cached.boundary,cached.token_type,cached.modifier],[plain.boundary,plain.token_type,plain.modifier]):
            torch.testing.assert_close(a,b,rtol=0,atol=0)

    def test_unicode_reference_fixture_matches_frozen_native_output(self):
        saved=json.loads(Path('tests/fixtures/window-fusion.json').read_text())
        self.assertEqual(saved,fixture())
