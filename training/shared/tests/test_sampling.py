from types import SimpleNamespace
import unittest

from training.shared.train import TrainingConfig, epoch_batches


class SamplingTests(unittest.TestCase):
    def test_full_window_sampler_covers_every_window_once(self):
        split = SimpleNamespace(refs=[{'stream': 'natural'}] * 5 + [{'stream': 'focus'}] * 17)
        config = TrainingConfig(batch_size=4, sampling='shuffled-windows')
        batches = epoch_batches(split, config, 1)
        self.assertEqual(sorted(i for batch in batches for i in batch), list(range(22)))
        self.assertEqual(batches, epoch_batches(split, config, 1))
        self.assertNotEqual(batches, epoch_batches(split, config, 2))

    def test_rotating_curriculum_preserves_natural_coverage(self):
        split = SimpleNamespace(refs=[{'stream': 'natural'}] * 5 + [{'stream': 'focus'}] * 17)
        config = TrainingConfig(batch_size=4, focus_batch_size=3)
        batches = epoch_batches(split, config, 1)
        self.assertEqual(sorted(i for batch in batches for i in batch if i < 5), list(range(5)))
        self.assertEqual(len([i for batch in batches for i in batch if i >= 5]), 6)
