"""Pure regression tests for struct-tag diagnostic classification."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("diagnose_struct_tags", ROOT / "diagnose_struct_tags.py")
module = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT))
assert spec.loader is not None
spec.loader.exec_module(module)


class StructTagDiagnosticTests(unittest.TestCase):
    def test_exact_split_and_role_mismatch(self) -> None:
        source = '`json:"name" gorm:"column:name"`'
        gold = {"start": 0, "end": len(source), "tokenType": "string"}
        exact = [dict(gold)]
        self.assertEqual(module.classify_gold_string(source, gold, exact)["kind"], "exact")
        split = [
            {"start": 0, "end": 12, "tokenType": "string"},
            {"start": 13, "end": len(source), "tokenType": "string"},
        ]
        self.assertEqual(module.classify_gold_string(source, gold, split)["kind"], "split")
        mismatch = [{"start": 0, "end": len(source), "tokenType": "variable"}]
        self.assertEqual(module.classify_gold_string(source, gold, mismatch)["kind"], "role-mismatch")

    def test_truncated_and_overextended(self) -> None:
        source = 'x`json:"id"`y'
        gold = {"start": 1, "end": len(source) - 1, "tokenType": "string"}
        truncated = [{"start": 2, "end": len(source) - 2, "tokenType": "string"}]
        overextended = [{"start": 0, "end": len(source), "tokenType": "string"}]
        self.assertEqual(module.classify_gold_string(source, gold, truncated)["kind"], "truncated")
        self.assertEqual(module.classify_gold_string(source, gold, overextended)["kind"], "overextended")

    def test_utf16_slice_handles_emoji(self) -> None:
        source = 'a😀b'
        self.assertEqual(module.utf16_slice(source, 1, 3), '😀')
        self.assertEqual(module.utf16_slice(source, 3, 4), 'b')


if __name__ == "__main__":
    unittest.main()
