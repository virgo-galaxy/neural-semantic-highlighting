import hashlib,json,tempfile,unittest
from pathlib import Path
from packs.rust.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class RustTeacherTests(unittest.TestCase):
    def test_independent_golden_and_original_utf16(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                g=unmark(case['markedSource']);r=label(source=g['source']);self.assertEqual(r['spans'],g['spans']);encode(dict(source=g['source'],documentKind='rust',result=r,contentHash=hashlib.sha256(g['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_lifetimes_are_not_char_literals(self):
        source="fn f<'a>(x: &'a str) -> &'a str { let c = 'a'; x }";r=label(source=source);items=[(source[s['start']:s['end']],s['tokenType']) for s in r['spans']];self.assertEqual(items.count(("'a",'type-parameter')),3);self.assertIn(("'a'",'string'),items)
    def test_parameters_and_shadowed_scopes_do_not_leak(self):
        s='fn f(value: i32) { let cb = |other| other + value; } fn g() { let value = 1; }';r=label(source=s);tail=s.rindex('value');self.assertIn(dict(start=tail,end=tail+5,tokenType='variable',modifiers=['declaration']),r['spans']);self.assertTrue(any(s[x['start']:x['end']]=='other' and x['tokenType']=='parameter' and not x.get('modifiers') for x in r['spans']))
    def test_macro_expansion_is_not_fabricated(self):
        s='macro_rules! twice { ($x:expr) => { $x + $x }; } fn main(){ twice!(2); }';r=label(source=s);self.assertEqual(sum(x['tokenType']=='parameter' for x in r['spans']),3);self.assertEqual(sum(x['tokenType']=='function' and s[x['start']:x['end']]=='twice' for x in r['spans']),2)
    def test_hidden_macro_repetition_separators_are_covered(self):
        s='macro_rules! collect { ($($x:expr),*) => { [$($x),*] }; }';r=label(source=s);commas=[x for x in r['spans'] if s[x['start']:x['end']]==','];self.assertEqual(len(commas),2);self.assertTrue(all(x['tokenType']=='punctuation' for x in commas));encode(dict(source=s,documentKind='rust',result=r,contentHash=hashlib.sha256(s.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_source_modules_and_builds_are_not_executed(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'never-created';s='mod missing; fn main(){ std::fs::write('+json.dumps(str(target))+', "bad").unwrap(); }';self.assertTrue(label(source=s)['spans']);self.assertFalse(target.exists())
    def test_raw_unicode_comments_and_bom_preserve_coordinates(self):
        s='\ufeffconst TEXT: &str = r##"星 🌌 /* not a comment */"##;\r\n/* outer /* inner */ end */\r\n';r=label(source=s);self.assertEqual(r['spans'][0],dict(start=0,end=1,tokenType='punctuation'));self.assertEqual(sum(x['tokenType']=='comment' for x in r['spans']),1);encode(dict(source=s,documentKind='rust',result=r,contentHash=hashlib.sha256(s.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_invalid_grammar_and_scope_are_quarantined(self):
        for s in ['fn broken( {','fn main(){ let x="unclosed; }']:
            with self.assertRaises(ValueError):label(source=s)
        with self.assertRaises(ValueError):label(source='fn main(){}',document_kind='cpp')
        self.assertEqual(label(source='')['spans'],[])
if __name__=='__main__':unittest.main()
