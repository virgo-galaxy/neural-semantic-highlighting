from types import SimpleNamespace
import unittest

import torch

from training.shared.trainer_data import training_weights


class TrainingWeightTests(unittest.TestCase):
    def test_natural_class_balance_excludes_authored_curriculum(self):
        natural=dict(boundary_labels=[1,2,0],token_type_labels=[0,0,-100],modifier_bits=[0,0,0])
        focus=dict(boundary_labels=[1]+[2]*19,token_type_labels=[1]*20,modifier_bits=[1]+[0]*19)
        split=SimpleNamespace(rows=[natural,focus],refs=[dict(stream='natural'),dict(stream='focus')],
            snapshot=SimpleNamespace(schema=dict(tokenTypes=['string','namespace'],modifiers=['declaration'])))
        real=training_weights(split,stream='natural');combined=training_weights(split)
        torch.testing.assert_close(real['token_type'],torch.ones(2))
        self.assertGreater(float(combined['token_type'][0]),float(combined['token_type'][1]))
        self.assertEqual(float(real['modifier'][0]),1.)

    def test_rejects_unknown_or_empty_training_weight_selection(self):
        split=SimpleNamespace(rows=[],refs=[],snapshot=SimpleNamespace(schema=dict(tokenTypes=['string'],modifiers=['declaration'])))
        for stream in ['test','natural','all']:
            with self.subTest(stream=stream),self.assertRaises(ValueError):training_weights(split,stream=stream)


if __name__=='__main__':unittest.main()
