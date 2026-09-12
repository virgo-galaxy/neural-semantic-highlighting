"""Pure regression tests for function-range method diagnostic classification."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("diagnose_function_range", ROOT / "diagnose_function_range.py")
module = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT))
assert spec.loader is not None
spec.loader.exec_module(module)


class FunctionRangeDiagnosticTests(unittest.TestCase):
    def test_exact_and_wrong_role_same_range(self) -> None:
        source = "items.Each"
        gold = {"start": 6, "end": 10, "tokenType": "method"}
        exact = [dict(gold)]
        self.assertEqual(module.classify_gold_method(source, gold, exact)["kind"], "exact")
        wrong = [{"start": 6, "end": 10, "tokenType": "property"}]
        result = module.classify_gold_method(source, gold, wrong)
        self.assertEqual(result["kind"], "wrong-role")
        self.assertEqual(result["sameRangePredictions"][0]["tokenType"], "property")

    def test_missing_role_mismatch_and_split(self) -> None:
        source = "iterator.Value"
        gold = {"start": 9, "end": 14, "tokenType": "method"}
        self.assertEqual(module.classify_gold_method(source, gold, [])["kind"], "missing")
        mismatch = [{"start": 9, "end": 14, "tokenType": "function"}]
        self.assertEqual(module.classify_gold_method(source, gold, mismatch)["kind"], "wrong-role")
        split = [
            {"start": 9, "end": 11, "tokenType": "method"},
            {"start": 11, "end": 14, "tokenType": "method"},
        ]
        self.assertEqual(module.classify_gold_method(source, gold, split)["kind"], "split")

    def test_truncated_and_overextended(self) -> None:
        source = "obj.Iterate()"
        gold = {"start": 4, "end": 11, "tokenType": "method"}
        truncated = [{"start": 5, "end": 10, "tokenType": "method"}]
        overextended = [{"start": 3, "end": 12, "tokenType": "method"}]
        self.assertEqual(module.classify_gold_method(source, gold, truncated)["kind"], "truncated")
        self.assertEqual(module.classify_gold_method(source, gold, overextended)["kind"], "overextended")

    def test_aggregate_counts_wrong_roles_by_family(self) -> None:
        docs = [
            {
                "family": "function-range/validation/pointer-method",
                "goldMethodCount": 2,
                "exactMethodCount": 1,
                "cases": [
                    {"kind": "exact", "sameRangePredictions": [], "overlappingPredictions": []},
                    {
                        "kind": "wrong-role",
                        "sameRangePredictions": [{"tokenType": "property"}],
                        "overlappingPredictions": [{"tokenType": "property"}],
                    },
                ],
                "extraPredictedMethods": [],
            }
        ]
        report = module.aggregate(docs)
        self.assertEqual(report["goldMethods"], 2)
        self.assertEqual(report["exactMethods"], 1)
        self.assertEqual(report["wrongRolePredictions"], {"property": 1})
        self.assertEqual(report["families"]["function-range/validation/pointer-method"]["wrong-role"], 1)


if __name__ == "__main__":
    unittest.main()
