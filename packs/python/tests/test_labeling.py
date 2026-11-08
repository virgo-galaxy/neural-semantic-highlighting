"""Independent compiler-teacher checks; run with pinned modern Gold Python."""
import json
from pathlib import Path
import sys
import unittest
from packs.python.labeling.label import label
from training.shared.golden import unmark

class TeacherTests(unittest.TestCase):
    def test_independent_marked_golden(self):
        cases=json.loads((Path(__file__).parents[1]/'fixtures/golden.json').read_text())
        for case in cases:
            if case['id']=='whole-adjacent-strings' and sys.version_info < (3,14):continue
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource'])
                self.assertEqual(label(source=gold['source'])['spans'],gold['spans'])

    def test_source_is_never_executed(self):
        source='raise RuntimeError("must not execute")\nimport unavailable_secret_package\n'
        self.assertTrue(label(source=source)['spans'])

    def test_invalid_source_fails(self):
        with self.assertRaises(SyntaxError):label(source='def broken(:\n')

    def test_unbound_class_namespace_is_not_function_scope(self):
        source='class Item:\n    len = 2\n    def size(self):\n        return len([])\n'
        result=label(source=source);raw=source.encode('utf-16-le')
        names=[s for s in result['spans'] if raw[s['start']*2:s['end']*2].decode('utf-16-le')=='len']
        self.assertEqual(names[-1]['tokenType'],'function')
        self.assertEqual(names[-1]['modifiers'],['default-library'])

if __name__=='__main__':unittest.main()
