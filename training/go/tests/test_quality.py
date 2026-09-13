from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quality import (MIN_ROLE_SUPPORT, TARGET_F1, TARGETED_ROLES,
                     natural_role_gate_summary, quality_gate_summary, targeted_gate_passed, targeted_scores)


class QualityGateTests(unittest.TestCase):
    @staticmethod
    def report(score: float = .91, support: int = 64) -> dict:
        token_types = {
            "keyword": {"f1": .99, "support": 1000},
            "string": {"f1": .93, "support": 200},
            "method": {"f1": .95, "support": 300},
            "label": {"f1": .70, "support": 8},
        }
        return {
            "streams": {
                "natural": {"exactSpan": {"f1": .97}, "exactSpanMacroF1": .94, "byTokenType": token_types},
                "focus": {"exactSpan": {"f1": .99}},
            },
            "focusFeatures": {
                feature: {"byTokenType": {role: {"f1": score, "support": support}}}
                for feature, role in TARGETED_ROLES.items()
            },
        }

    def test_targeted_roles_include_string_robustness(self):
        self.assertEqual(TARGETED_ROLES["strings"], "string")
        self.assertTrue(targeted_gate_passed(self.report()))
        self.assertEqual(TARGET_F1, .90)

    def test_all_targeted_roles_must_reach_gate_with_real_support(self):
        report = self.report()
        report["focusFeatures"]["self-reference"]["byTokenType"]["interface"]["f1"] = .8999
        self.assertFalse(targeted_gate_passed(report))
        report = self.report(support=MIN_ROLE_SUPPORT - 1)
        self.assertFalse(targeted_gate_passed(report))

    def test_missing_target_is_not_a_pass(self):
        report = self.report()
        del report["focusFeatures"]["generic-method"]
        self.assertFalse(targeted_gate_passed(report))
        rows = {row["feature"]: row for row in targeted_scores(report)}
        self.assertIsNone(rows["generic-method"]["f1"])
        self.assertEqual(rows["generic-method"]["support"], 0)

    def test_natural_gate_ignores_only_low_support_roles(self):
        report = self.report()
        self.assertTrue(natural_role_gate_summary(report)["passed"])
        report["streams"]["natural"]["byTokenType"]["string"]["f1"] = .89
        self.assertFalse(natural_role_gate_summary(report)["passed"])

    def test_quality_gate_combines_aggregate_natural_and_targeted_checks(self):
        report = self.report()
        self.assertTrue(quality_gate_summary(report)["passed"])
        report["streams"]["natural"]["byTokenType"]["string"]["f1"] = .89
        self.assertFalse(quality_gate_summary(report)["passed"])
        report = self.report()
        report["focusFeatures"]["struct-tags"]["byTokenType"]["string"]["f1"] = .80
        self.assertFalse(quality_gate_summary(report)["passed"])


if __name__ == "__main__":
    unittest.main()
