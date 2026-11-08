import hashlib
import json
from pathlib import Path
import unittest

from packs.assembly.labeling.label import label
from training.shared.encoding import Schema, encode
from training.shared.golden import unmark


class AssemblyTeacherTests(unittest.TestCase):
    def test_independent_golden_and_original_coordinates(self):
        root = Path(__file__).parents[1]
        for case in json.loads((root / 'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                expected = unmark(case['markedSource'])
                result = label(source=expected['source'], profile=case['profile'])
                self.assertEqual(result['spans'], expected['spans'])
                encode({'source': expected['source'], 'documentKind': 'assembly', 'result': result,
                        'contentHash': hashlib.sha256(expected['source'].encode()).hexdigest()}, Schema.load(root / 'schema.json'))

    def test_same_source_has_same_roles_across_profiles(self):
        sources = ['ret\n', 'mov rax, rdi ; source note\n', 'add x0, x0, #1 // amount\n', '.asciz "record"\n']
        for source in sources:
            with self.subTest(source=source):
                expected = label(source=source, profile='nasm')['spans']
                for profile in ['gas', 'masm', 'aarch64']:
                    self.assertEqual(label(source=source, profile=profile)['spans'], expected)

    def test_hash_comment_and_immediate_are_distinct(self):
        source = 'movq $4, %rax # number\nadd x0, x0, # 4 // immediate\n'
        raw = source.encode('utf-16-le')
        spans = label(source=source, profile='aarch64')['spans']
        comments = [raw[s['start'] * 2:s['end'] * 2].decode('utf-16-le') for s in spans if s['tokenType'] == 'comment']
        self.assertEqual(comments, ['# number', '// immediate'])
        self.assertEqual(sum(s['tokenType'] == 'operator' and raw[s['start'] * 2:s['end'] * 2].decode('utf-16-le') == '#' for s in spans), 1)

    def test_size_operand_does_not_turn_mnemonic_into_declaration(self):
        spans = label(source='mov qword [rax], 1\n')['spans']
        self.assertEqual(spans[0], {'start': 0, 'end': 3, 'tokenType': 'keyword'})

    def test_source_and_include_are_never_executed(self):
        self.assertTrue(label(source='%include "never-open-this.inc"\nstart:\n syscall\n')['spans'])


if __name__ == '__main__':
    unittest.main()
