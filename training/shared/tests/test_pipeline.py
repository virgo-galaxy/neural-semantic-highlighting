"""Shared invariants that prevent leakage and incompatible model promotion."""
from array import array
from collections import Counter
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import torch
from training.shared.encoding import Schema, encode, windows
from training.shared.prepare import assign_groups
from training.shared.prepare import training_feature_coverage
from training.shared.spec import using, current
from training.shared.checkpoints import load_checkpoint, save_checkpoint
from training.shared.inference import decode
from training.shared.model import ModelOutput

class PipelineTests(unittest.TestCase):
    def record(self,source,spans):
        return {'source':source,'contentHash':hashlib.sha256(source.encode()).hexdigest(),'documentKind':'python',
                'result':{'offsetEncoding':'utf-16','spans':spans}}

    def test_utf16_original_bytes_and_fixed_cuts(self):
        source='"🌌 abc"';spans=[{'start':0,'end':len(source)+1,'tokenType':'string'}]
        encoded=encode(self.record(source,spans),Schema(('string',),()))
        self.assertEqual(list(encoded.columns['input_ids']),list(source.encode()))
        fixed,_=windows(encoded,6,adaptive=False)
        self.assertEqual(fixed,[(0,6),(6,len(source.encode()))])
        for a,b in fixed:source.encode()[a:b].decode('utf-8')
        bad=self.record(source,[{'start':0,'end':2,'tokenType':'string'}])
        with self.assertRaises(ValueError):encode(bad,Schema(('string',),()))

    def test_nonwhite_gold_gaps_are_rejected(self):
        with self.assertRaises(ValueError):encode(self.record('x=1',[{'start':0,'end':1,'tokenType':'variable'}]),Schema(('variable',),()))

    def test_renamed_copies_have_same_shape(self):
        schema=Schema(('variable','operator','number'),())
        def sample(name):
            source=name+'=1';n=len(name)
            return encode(self.record(source,[{'start':0,'end':n,'tokenType':'variable'},{'start':n,'end':n+1,'tokenType':'operator'},{'start':n+1,'end':n+2,'tokenType':'number'}]),schema)
        self.assertEqual(sample('alpha').shape_hash,sample('beta').shape_hash)

    def test_grouped_split_coverage(self):
        weights={f'g{i}':Counter({'python:natural':i+1}) for i in range(12)}
        result=assign_groups(weights,1729)
        self.assertEqual(set(result.values()),{'train','validation','test'})
        self.assertEqual(result,assign_groups(dict(reversed(list(weights.items()))),1729))
        with self.assertRaises(ValueError):assign_groups({'a':Counter(x=1),'b':Counter(x=2)},1)

    def test_context_is_restored(self):
        with using('python') as outer:
            with using('python') as inner:
                self.assertIs(current(),inner)
                self.assertIsNot(inner,outer)
            self.assertIs(current(),outer)

    def test_inference_artifact_cannot_resume(self):
        with tempfile.TemporaryDirectory() as temporary, using('python'):
            path=Path(temporary)/'model.pt';save_checkpoint(path,{'format':current().model_format})
            with self.assertRaises(ValueError):load_checkpoint(path)

    def test_code_modifiers_survive_neural_decoder(self):
        out=ModelOutput(torch.tensor([[0.,9.,0.]]),torch.tensor([[9.]]),torch.tensor([[9.]]))
        result=decode('x',out,{'tokenTypes':['function'],'modifiers':['declaration']})
        self.assertEqual(result['spans'],[{'start':0,'end':1,'tokenType':'function','modifiers':['declaration']}])

    def test_pack_string_canonicalization_uses_predicted_ranges_only(self):
        schema={'tokenTypes':['string','variable'],'modifiers':['declaration']}
        out=ModelOutput(torch.tensor([[0.,9.,0.]]*4),torch.tensor([[9.,0.],[9.,0.],[0.,9.],[0.,9.]]),torch.tensor([[-9.]]*4))
        baseline=decode('abcd',out,schema)
        canonical=decode('abcd',out,schema,coalesce_types=('string',))
        self.assertEqual(len(baseline['spans']),4)
        self.assertEqual([(s['start'],s['end'],s['tokenType']) for s in canonical['spans']],[(0,2,'string'),(2,3,'variable'),(3,4,'variable')])
        gap=ModelOutput(torch.tensor([[0.,9.,0.],[9.,0.,0.],[0.,9.,0.]]),torch.tensor([[9.,0.]]*3),torch.tensor([[-9.]]*3))
        self.assertEqual(len(decode('a b',gap,schema,coalesce_types=('string',))['spans']),2)

    def test_modifier_role_validity_and_policy_binding(self):
        out=ModelOutput(torch.tensor([[0.,9.,0.]]),torch.tensor([[9.]]),torch.tensor([[9.]]))
        schema={'tokenTypes':['string'],'modifiers':['declaration']}
        self.assertNotIn('modifiers',decode('x',out,schema,modifier_roles={'declaration':('function',)})['spans'][0])
        with using('bash'):
            with self.assertRaises(ValueError):current().verify_config({})
        with using('python'):current().verify_config({})

    def test_feature_coverage_cannot_be_supplied_by_a_holdout(self):
        with using('bash'):
            records=[];assignments={}
            for profile in current().profiles:
                for index in range(3):
                    group=f'{profile}/{index}';assignments[group]='train'
                    records.append({'profile':profile,'sourceGroup':group,'features':list(dict(current().required_training_features)[profile])})
            coverage=training_feature_coverage(records,assignments)
            self.assertEqual(len(coverage['csh']['loops']['sourceGroups']),3)
            assignments['csh/0']='test'
            with self.assertRaisesRegex(ValueError,'Insufficient independent training groups'):
                training_feature_coverage(records,assignments)

if __name__=='__main__':unittest.main()
