from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from packs.makefile.labeling.label import label
from training.shared.encoding import Schema, encode
from training.shared.golden import unmark


class MakefileLabelingTests(unittest.TestCase):
    def parts(self, source, role):
        raw=source.encode('utf-16-le')
        return [raw[s['start']*2:s['end']*2].decode('utf-16-le') for s in label(source=source)['spans'] if s['tokenType']==role]

    def test_independent_marked_golden(self):
        for case in json.loads((Path(__file__).parents[1]/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);self.assertEqual(label(source=gold['source'])['spans'],gold['spans'])

    def test_source_includes_shell_eval_and_recipes_never_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'must-not-exist'
            source='include '+str(target)+'\nX := $(shell touch '+str(target)+')\n$(eval X = unused)\nall:\n\ttouch '+str(target)+'\n'
            label(source=source);self.assertFalse(target.exists())

    def test_make_comments_ignore_quotes_and_continue(self):
        source='X = "value # original"\n# still \\\n comment\n'
        self.assertEqual(self.parts(source,'comment'),['# original"','# still \\\n comment'])

    def test_hash_in_functions_and_escaped_hash_are_literal(self):
        source='X = $(subst #,x,$(VALUE))\nY = one\\#two\n'
        self.assertEqual(self.parts(source,'comment'),[])
        self.assertIn('one\\#two',self.parts(source,'string'))

    def test_make_and_recipe_continuations_keep_context(self):
        source='FILES = one \\\n\t# comment\nall:\n\tfor value in one two; do \\\n\t echo "$$value"; done\n'
        self.assertEqual(self.parts(source,'comment'),['# comment'])
        self.assertIn('$$value',self.parts(source,'variable'))
        self.assertIn('for',self.parts(source,'keyword'))

    def test_escaped_shell_and_make_variables_retain_ranges(self):
        source='all:\n\t@echo "$$HOME $(ROOT)"; echo $$(date)\n'
        self.assertIn('$$HOME',self.parts(source,'variable'))
        self.assertIn('$(ROOT)',self.parts(source,'variable'))
        self.assertIn('date',self.parts(source,'function'))

    def test_define_body_is_opaque_original_source(self):
        source='define BODY\n# literal\n.RECIPEPREFIX = >\necho $(VALUE)\nendef\nall:\n\techo ready\n'
        self.assertIn('# literal\n.RECIPEPREFIX = >\necho $(VALUE)\n',self.parts(source,'string'))
        self.assertEqual(self.parts(source,'comment'),[])

    def test_literal_recipe_prefix_and_reset(self):
        source='.RECIPEPREFIX = >\nall:\n>@echo ready\n.RECIPEPREFIX =\nother:\n\t@echo done\n'
        self.assertEqual(self.parts(source,'function'),['echo','echo'])
        self.assertIn('>',self.parts(source,'punctuation'))

    def test_foreign_or_computed_shell_is_opaque(self):
        for value in ['cmd.exe','$(CUSTOM_SHELL)']:
            source='SHELL := '+value+'\nall:\n\techo "$HOME"\n'
            with self.subTest(value=value):
                self.assertEqual(self.parts(source,'function'),[])
                self.assertIn('echo "$HOME"',self.parts(source,'string'))

    def test_bom_unicode_crlf_and_final_newline_are_preserved(self):
        source='\ufeff# 原文 🌌\r\nTITLE = "你好 🌌"\r\nall:\r\n\t@echo "$$HOME"'
        result=label(source=source)
        record=dict(source=source,documentKind='makefile',contentHash=hashlib.sha256(source.encode()).hexdigest(),result=result)
        encoded=encode(record,Schema.load(Path(__file__).parents[1]/'schema.json'))
        self.assertEqual(bytes(encoded.columns['input_ids'].tolist()),source.encode())
        self.assertIn('"你好 🌌"',self.parts(source,'string'))

    def test_invalid_source_and_unsupported_dynamic_prefix_are_rejected(self):
        for source in ['X = value\x00','all:\r\techo ready','ifdef DEBUG\nX = 1\n','ifeq ($(X),1)\n.RECIPEPREFIX = >\nendif\nall:\n>echo ready\n','not a rule\n','!IF DEBUG\n!ENDIF\n']:
            with self.subTest(source=source),self.assertRaises(ValueError):label(source=source)

    def test_explicit_kind_profile_and_empty_input(self):
        self.assertEqual(label(source='')['spans'],[])
        for values in [dict(document_kind='cmake'),dict(profile='nmake')]:
            with self.assertRaises(ValueError):label(source='all:\n',**values)


if __name__=='__main__':unittest.main()
