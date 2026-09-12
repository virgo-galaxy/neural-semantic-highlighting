from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sealed_eval import MIN_ROLE_SUPPORT, MIN_TARGET_SUPPORT, acceptance, role_gate, targeted_gate


class SealedEvaluationTests(unittest.TestCase):
    def token_report(self, *, good: bool = True) -> dict:
        roles = {}
        for name in [
            "keyword", "comment", "string", "number", "operator", "punctuation", "namespace", "type",
            "interface", "type-parameter", "function", "method", "parameter", "variable", "property", "label",
        ]:
            roles[name] = {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": MIN_ROLE_SUPPORT,
                           "fp": 0, "fn": 0, "support": MIN_ROLE_SUPPORT}
        if not good:
            roles["method"] = {"precision": .8, "recall": .8, "f1": .8, "tp": 24, "fp": 6, "fn": 6,
                               "support": MIN_ROLE_SUPPORT}
        return {
            "exactSpan": {"f1": .98},
            "exactSpanMacroF1": .97,
            "exactSpanIncludingModifiers": {"f1": .97},
            "byTokenType": roles,
        }

    def focus_features(self, *, good: bool = True) -> dict:
        result = {}
        roles = {
            "self-reference": "interface",
            "function-range": "method",
            "generic-method": "method",
            "generic-alias": "type-parameter",
            "struct-tags": "string",
        }
        for feature, role in roles.items():
            f1 = 1.0
            if not good and feature == "function-range":
                f1 = .85
            result[feature] = {"byTokenType": {role: {"f1": f1, "support": MIN_TARGET_SUPPORT}}}
        return result

    def test_role_gate_ignores_zero_and_reports_low_support(self):
        report = self.token_report()
        report["byTokenType"]["label"]["support"] = 3
        report["byTokenType"]["label"]["f1"] = .0
        gate = role_gate(report)
        self.assertTrue(gate["passed"])
        self.assertIn("label", gate["lowSupportRoles"])

    def test_targeted_gate_requires_support_and_f1(self):
        self.assertTrue(targeted_gate(self.focus_features())["passed"])
        weak = self.focus_features()
        weak["struct-tags"]["byTokenType"]["string"]["support"] = MIN_TARGET_SUPPORT - 1
        self.assertFalse(targeted_gate(weak)["passed"])
        self.assertFalse(targeted_gate(self.focus_features(good=False))["passed"])

    def test_acceptance_combines_aggregate_and_role_gates(self):
        report = {"streams": {"natural": self.token_report(), "focus": {"exactSpan": {"f1": .99},
                  "exactSpanMacroF1": .99, "exactSpanIncludingModifiers": {"f1": .99}, "byTokenType": {}}},
                  "focusFeatures": self.focus_features()}
        self.assertTrue(acceptance(report)["passed"])
        report["streams"]["natural"]["exactSpan"]["f1"] = .90
        self.assertFalse(acceptance(report)["passed"])


if __name__ == "__main__":
    unittest.main()
