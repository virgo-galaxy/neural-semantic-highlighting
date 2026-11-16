from pathlib import Path
import copy
import json
import unittest

import torch

from training.shared.inference import character_map, decode
from training.shared.model import ModelOutput
from training.shared.structured import fit, validate


class StructuredTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((Path(__file__).resolve().parents[3] / 'tests/fixtures/joint-bio.json').read_text())

    def test_unicode_joint_path_repairs_a_false_begin_and_preserves_start_flags(self):
        f = self.fixture
        starts, _ = character_map(f['source'])
        values = []
        for name, width in [('boundary', 3), ('token', 2), ('modifier', 1)]:
            logits = torch.zeros(starts[-1], width)
            for a, row in zip(starts[:-1], f[name]):
                logits[a] = torch.tensor(row)
            values.append(logits)
        out = ModelOutput(*values)
        result = decode(f['source'], out, f['schema'], structured_decoder=f['parameters'],
                        modifier_roles={'strong': ['text']})
        self.assertEqual(result, f['expected'])
        self.assertNotEqual(decode(f['source'], out, f['schema']), result)
        self.assertEqual(decode('', ModelOutput(torch.empty(0, 3), torch.empty(0, 2), torch.empty(0, 1)),
                                f['schema'], structured_decoder=f['parameters'])['spans'], [])

    def test_rejects_bad_role_order_illegal_inside_states_and_nonfinite_scores(self):
        f = self.fixture
        for change in ('roles', 'inside', 'initial', 'weight', 'dimension'):
            p = copy.deepcopy(f['parameters'])
            if change == 'roles': p['tokenTypes'].reverse()
            if change == 'inside': p['transitions'][0][2] = -1
            if change == 'initial': p['initial'][2] = -1
            if change == 'weight': p['typeWeight'] = float('nan')
            if change == 'dimension': p['transitions'].pop()
            with self.assertRaises(ValueError): validate(p, f['schema'])

    def test_transition_fitting_requires_explicit_natural_training_records(self):
        with self.assertRaises(ValueError):
            fit([{'stream': 'focus'}], self.fixture['schema'], type_weight=.25, transition_weight=.5)


if __name__ == '__main__': unittest.main()
