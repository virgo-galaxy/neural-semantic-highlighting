import hashlib,json,unittest
from pathlib import Path
from packs.dart.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]

class DartTeacherTests(unittest.TestCase):
    def test_independent_marked_golden_original_utf16(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);result=label(source=gold['source'])
                self.assertEqual(result['spans'],gold['spans'])
                if gold['source']:encode(dict(source=gold['source'],documentKind='dart',result=result,contentHash=hashlib.sha256(gold['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_catch_payload_scope_includes_only_its_body(self):
        source='void f() { try {} catch(error,stack) { print(error); } print(error); }'
        spans=label(source=source)['spans']
        first=source.index('error);');last=source.rindex('error);')
        self.assertIn(dict(start=first,end=first+5,tokenType='parameter'),spans)
        self.assertIn(dict(start=last,end=last+5,tokenType='variable'),spans)
    def test_block_shadowing_and_generic_return_type(self):
        source='T id<T>(T value) { { final value=1; print(value); } return value; }'
        spans=label(source=source)['spans']
        self.assertEqual(spans[0],dict(start=0,end=1,tokenType='type-parameter'))
        at=source.index('value);');self.assertIn(dict(start=at,end=at+5,tokenType='variable'),spans)
        at=source.rindex('value;');self.assertIn(dict(start=at,end=at+5,tokenType='parameter'),spans)
    def test_raw_strings_are_not_interpolated_or_rescanned_as_comments(self):
        source='const text=r"$name // ${missing}"; // outside\n'
        spans=label(source=source)['spans']
        self.assertEqual(sum(s['tokenType']=='string' for s in spans),1)
        self.assertEqual(sum(s['tokenType']=='comment' for s in spans),1)
        self.assertNotIn('interpolation',label(source=source)['features'])
    def test_interpolation_keeps_expression_and_named_member_roles(self):
        source='String f(String name) => "Hi ${name.length}!";'
        spans=label(source=source)['spans'];at=source.index('name.length')
        self.assertIn(dict(start=at,end=at+4,tokenType='parameter'),spans)
        at=source.index('length');self.assertIn(dict(start=at,end=at+6,tokenType='property'),spans)
    def test_const_initializer_does_not_make_final_binding_constant(self):
        source='void f() { final value=const Missing(); }';at=source.index('value')
        self.assertIn(dict(start=at,end=at+5,tokenType='variable',modifiers=['declaration']),label(source=source)['spans'])
    def test_imports_annotations_and_input_never_execute(self):
        source="import 'missing-file.dart'; @Missing('do not run') void main() { throw 'not executed'; }"
        self.assertTrue(label(source=source)['spans'])
    def test_current_syntax_and_flutter_calls_need_no_sdk(self):
        for source in ['class Point(var int x, var int y);','extension type Id(int value) {}','void f(Object x) { if(x case [int v]) print(v); }','Widget f() => Column(children: [Text("Hi"), const SizedBox(height: 2)]);']:
            self.assertTrue(label(source=source)['spans'])
    def test_invalid_input_fails_closed(self):
        for source in ['void f( {','const x="unfinished;', 'void f() {\0}']:
            with self.assertRaises(ValueError):label(source=source)
        with self.assertRaises(ValueError):label(source='',document_kind='flutter')
        self.assertEqual(label(source='')['spans'],[])

if __name__=='__main__':unittest.main()
