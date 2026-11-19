import unittest

from training.shared.export_model import calibration_selection


class CalibrationExportTests(unittest.TestCase):
    def test_accepts_legacy_and_indexed_validation_evidence(self):
        self.assertEqual(calibration_selection(dict(primaryTestUsed=False,selected=dict(selectionScore=.8))),.8)
        self.assertEqual(calibration_selection(dict(testUsed=False,selected=0,trials=[dict(index=0,selectionKey=[.9,.8])])),.9)

    def test_rejects_test_use_bad_index_and_nonfinite_score(self):
        for report in [dict(primaryTestUsed=True,selected=dict(selectionScore=.8)),
                       dict(selected=dict(selectionScore=.8)),
                       dict(testUsed=False,selected=True,trials=[]),
                       dict(testUsed=False,selected=1,trials=[]),
                       dict(testUsed=False,selected=dict(selectionScore=float('nan')))]:
            with self.assertRaises(ValueError):calibration_selection(report)
