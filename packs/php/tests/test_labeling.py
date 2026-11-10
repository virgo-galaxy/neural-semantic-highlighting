import hashlib,json,tempfile,unittest
from pathlib import Path
from packs.php.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class PhpTeacherTests(unittest.TestCase):
    def test_independent_golden_and_original_coordinates(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);r=label(source=gold['source']);self.assertEqual(r['spans'],gold['spans']);encode(dict(source=gold['source'],documentKind='php',result=r,contentHash=hashlib.sha256(gold['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_interpolation_preserves_parameter_and_nowdoc_is_opaque(self):
        source='<?php function f($name) { return "Hello {$name}"; } $raw=<<<\'TXT\'\n$name remains text\nTXT;'
        r=label(source=source);self.assertEqual([s['tokenType'] for s in r['spans'] if source[s['start']:s['end']]=='$name'],['parameter','parameter']);self.assertTrue(any(source[s['start']:s['end']]=='$name remains text' and s['tokenType']=='string' for s in r['spans']))
    def test_bom_original_coordinates(self):
        source='\ufeff<?php\r\n$x="星空 🌌";';r=label(source=source);self.assertEqual(r['spans'][0],dict(start=0,end=1,tokenType='punctuation'));self.assertEqual(r['spans'][1]['start'],1)
    def test_tags_in_a_tagless_string_do_not_change_grammar(self):
        source='$text = "<?php";';r=label(source=source);self.assertFalse(any(s['tokenType']=='embedded-html' for s in r['spans']))
    def test_source_and_includes_are_not_executed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'never-created';source='<?php require "missing.php"; file_put_contents("'+str(path)+'", "bad");';self.assertTrue(label(source=source)['spans']);self.assertFalse(path.exists())
    def test_invalid_php_cannot_become_valid_html(self):
        for source in ['<?php class Broken {','$x = "unfinished;']:
            with self.assertRaises(ValueError):label(source=source)
        with self.assertRaises(ValueError):label(source='<?php $x=1;',document_kind='html')
        self.assertEqual(label(source='')['spans'],[])
if __name__=='__main__':unittest.main()
