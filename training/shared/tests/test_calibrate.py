import unittest

from training.shared.calibrate import selection_key, validate_partitions


class CalibrationTests(unittest.TestCase):
    def test_rejects_leakage_and_missing_dialect(self):
        train = [dict(stream='natural', sourceGroup='train', profile='bash')]
        validation = [dict(stream='natural', sourceGroup='validation', profile='bash')]
        validate_partitions(train, validation, ['bash'])
        with self.assertRaises(ValueError):
            validate_partitions(train, train, ['bash'])
        with self.assertRaises(ValueError):
            validate_partitions(train, validation, ['bash', 'zsh'])
        with self.assertRaises(ValueError):
            validate_partitions([dict(train[0], stream='focus')], validation, ['bash'])

    def test_selection_keeps_dialect_balance(self):
        reports = {'bash': dict(exactSpanMacroF1=.9, exactSpan=dict(f1=.95)),
                   'zsh': dict(exactSpanMacroF1=.7, exactSpan=dict(f1=.8))}
        self.assertEqual(selection_key(reports), (.8, .8))
        self.assertEqual(selection_key(reports, 'profile-f1'), (.875, .8))
        self.assertEqual(selection_key(reports, 'minimum-profile-f1'), (.8, .8))
