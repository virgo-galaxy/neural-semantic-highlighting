from pathlib import Path
import tempfile
import unittest

import torch

from training.shared.model import SemanticTransformer, ModelConfig
from training.shared.initialization import initialize_from_checkpoint
from training.shared.checkpoints import save_checkpoint
from training.shared.spec import using
from training.browser.model import BrowserTransformer


class RelativeAttentionTests(unittest.TestCase):
    def test_zero_initialization_preserves_parent_weights_and_logits(self):
        with using('python')as spec,tempfile.TemporaryDirectory()as temporary:
            schema=spec.schema();args=dict(width=8,heads=2,layers=1,feed_forward=16,dropout=0)
            original=SemanticTransformer(ModelConfig(**args),len(schema['tokenTypes']),len(schema['modifiers'])).eval()
            target=SemanticTransformer(ModelConfig(**args,relative_attention=True),len(schema['tokenTypes']),len(schema['modifiers'])).eval()
            path=Path(temporary)/'full.pt'
            save_checkpoint(path,dict(format=spec.checkpoint_format,model=original.state_dict(),modelConfig=original.config.to_dict(),schema=schema,
                epoch=1,dataset={},trainingConfig=dict(smoke=False),optimizer={},rng={},trainingState={}))
            initialize_from_checkpoint(target,path)
            for name,value in original.state_dict().items():torch.testing.assert_close(value,target.state_dict()[name],rtol=0,atol=0)
            ids=torch.tensor([[67,240,159,140,140,59]])
            with torch.inference_mode():
                a=original(ids,torch.ones_like(ids,dtype=torch.bool));b=target(ids,torch.ones_like(ids,dtype=torch.bool))
            for name in ['boundary','token_type','modifier']:torch.testing.assert_close(getattr(a,name),getattr(b,name),rtol=1e-5,atol=1e-5)

    def test_distance_bias_learns_and_matches_browser_graph(self):
        model=SemanticTransformer(ModelConfig(width=8,heads=2,layers=1,feed_forward=16,dropout=0,relative_attention=True),4,1)
        ids=torch.tensor([[67,240,159,140,140,59]])
        model(ids,torch.ones_like(ids,dtype=torch.bool)).token_type.square().sum().backward()
        self.assertGreater(float(model.relative_bias.grad.abs().sum()),0)
        with torch.no_grad():model.relative_bias.fill_(.01)
        model.eval()
        with torch.inference_mode():
            native=model(ids,torch.ones_like(ids,dtype=torch.bool));browser=BrowserTransformer(model)(ids)
        for expected,actual in zip([native.boundary,native.token_type,native.modifier],browser):
            torch.testing.assert_close(expected,actual,rtol=1e-5,atol=1e-5)
