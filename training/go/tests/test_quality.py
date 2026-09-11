from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quality import TARGET_F1, TARGETED_ROLES, targeted_gate_passed, targeted_scores


class QualityGateTests(unittest.TestCase):
    @staticmethod
    def report(score: float = .91, support: int = 10) -> dict:
        return {
            "focusFeatures": {
                feature: {"byTokenType": {role: {"f1": score, "support": support}}}
                for feature, role in TARGETED_ROLES.items()
            }
        }

    def test_all_targeted_roles_must_reach_gate(self):
        report = self.report()
        self.assertTrue(targeted_gate_passed(report))
        self.assertEqual(TARGET_F1, .90)
        report["focusFeatures"]["self-reference"]["byTokenType"]["interface"]["f1"] = .8999
        self.assertFalse(targeted_gate_passed(report))

    def test_missing_or_zero_support_is_not_a_pass(self):
        report = self.report()
        del report["focusFeatures"]["generic-method"]
        self.assertFalse(targeted_gate_passed(report))
        rows = {row["feature"]: row for row in targeted_scores(report)}
        self.assertIsNone(rows["generic-method"]["f1"])
        self.assertEqual(rows["generic-method"]["support"], 0)


if __name__ == "__main__":
    unittest.main()
