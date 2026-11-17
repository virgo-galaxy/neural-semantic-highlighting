from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from packs.dockerfile.labeling.label import label
from training.shared.encoding import Schema, encode
from training.shared.golden import unmark


class DockerfileLabelingTests(unittest.TestCase):
    def test_independent_marked_golden(self):
        for case in json.loads((Path(__file__).parents[1] / 'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold = unmark(case['markedSource'])
                self.assertEqual(label(source=gold['source'])['spans'], gold['spans'])

    def test_multiple_heredocs_keep_file_bodies_opaque(self):
        source = 'COPY <<FIRST <<SECOND /etc/\nFROM literal\nFIRST\nRUN literal\nSECOND\n'
        result = label(source=source)
        bodies = [source[s['start']:s['end']] for s in result['spans'] if s['tokenType'] == 'string']
        self.assertIn('FROM literal\n', bodies)
        self.assertIn('RUN literal\n', bodies)
        self.assertEqual(sum(s['tokenType'] == 'keyword' for s in result['spans']), 1)

    def test_run_heredoc_shell_crosses_blank_lines(self):
        source = 'RUN <<SCRIPT\necho first\n\necho second\nSCRIPT\n'
        result = label(source=source)
        self.assertEqual([source[s['start']:s['end']] for s in result['spans'] if s['tokenType']=='function'], ['echo','echo'])
        self.assertEqual(sum(s['tokenType']=='label' for s in result['spans']), 2)

    def test_onbuild_nested_flags_and_json(self):
        source='ONBUILD COPY --chown=1000:1000 ["one", "/srv/"]\n'
        result=label(source=source)
        self.assertIn('json-form', result['features'])
        self.assertEqual([source[s['start']:s['end']] for s in result['spans'] if s['tokenType']=='parameter'], ['--chown=1000:1000'])

    def test_empty_and_comment_continuation_lines_retain_positions(self):
        source='RUN echo one \\\n\n # original comment\n && echo two\n'
        result=label(source=source)
        self.assertEqual([source[s['start']:s['end']] for s in result['spans'] if s['tokenType']=='function'], ['echo','echo'])
        self.assertEqual([source[s['start']:s['end']] for s in result['spans'] if s['tokenType']=='comment'], ['# original comment'])

    def test_explicit_foreign_shell_is_opaque_and_from_resets_it(self):
        source='SHELL ["pwsh", "-Command"]\nRUN Write-Host "$env:NAME"\nFROM alpine\nRUN echo ready\n'
        result=label(source=source)
        strings=[source[s['start']:s['end']] for s in result['spans'] if s['tokenType']=='string']
        self.assertIn('Write-Host "$env:NAME"', strings)
        self.assertEqual([source[s['start']:s['end']] for s in result['spans'] if s['tokenType']=='function'], ['echo'])

    def test_shebang_heredoc_is_not_guessed_as_shell(self):
        source='RUN <<PYTHON\n#!/usr/bin/env python\nprint("FROM literal")\nPYTHON\n'
        result=label(source=source)
        self.assertEqual(sum(s['tokenType']=='function' for s in result['spans']), 0)
        self.assertIn('#!/usr/bin/env python\nprint("FROM literal")\n',[source[s['start']:s['end']] for s in result['spans'] if s['tokenType']=='string'])

    def test_bom_crlf_unicode_roundtrip_and_complete_coverage(self):
        source='\ufeff# 星空 🌌\r\nENV TITLE="你好 🌌"\r\nCOPY <<TEXT /tmp/note\r\n原文\r\nTEXT\r\n'
        result=label(source=source)
        record=dict(source=source,documentKind='dockerfile',contentHash=hashlib.sha256(source.encode()).hexdigest(),result=result)
        encoded=encode(record,Schema.load(Path(__file__).parents[1]/'schema.json'))
        self.assertEqual(bytes(encoded.columns['input_ids'].tolist()), source.encode('utf-8'))
        raw=source.encode('utf-16-le')
        self.assertIn('"你好 🌌"',[raw[s['start']*2:s['end']*2].decode('utf-16-le')for s in result['spans']])

    def test_invalid_source_is_rejected(self):
        for source in ['RUN <<EOF\nunclosed\n','FROM alpine\x00','FROM alpine\rRUN echo no','NOT_DOCKER source\n','# syntax=one\n# syntax=two\nFROM alpine\n']:
            with self.subTest(source=source), self.assertRaises(ValueError): label(source=source)

    def test_wrong_kind_and_profile_are_rejected(self):
        for values in [dict(document_kind='compose'),dict(profile='docker')]:
            with self.assertRaises(ValueError): label(source='FROM alpine\n',**values)

    def test_source_is_never_executed_or_fetched(self):
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/'must-not-exist'
            label(source='FROM alpine\nRUN touch '+str(target)+'\nADD https://example.invalid/source /tmp/\n')
            self.assertFalse(target.exists())

    def test_empty_and_comment_only_inputs(self):
        self.assertEqual(label(source='')['spans'],[])
        self.assertEqual(label(source='# Only source\n')['spans'],[dict(start=0,end=13,tokenType='comment')])


if __name__ == '__main__': unittest.main()
