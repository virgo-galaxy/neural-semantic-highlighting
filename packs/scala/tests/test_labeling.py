import hashlib,json,unittest
from pathlib import Path
from packs.scala.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class ScalaTeacherTests(unittest.TestCase):
    def test_independent_marked_golden_original_utf16(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);result=label(source=gold['source']);self.assertEqual(result['spans'],gold['spans'])
                if gold['source']:encode(dict(source=gold['source'],documentKind='scala',result=result,contentHash=hashlib.sha256(gold['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_nested_shadowing_and_function_scope(self):
        source='def f(value: Int) = { { val value = 2; println(value) }; value }\nvalue';spans=label(source=source)['spans']
        at=source.index('value }');self.assertIn(dict(start=at,end=at+5,tokenType='parameter'),spans)
        at=source.rindex('value');self.assertIn(dict(start=at,end=at+5,tokenType='variable'),spans)
    def test_all_generic_parameters_and_curried_arguments_are_in_scope(self):
        source='def f[A, B](value: A)(other: B): B = other';spans=label(source=source)['spans'];at=source.index(': B =')+2
        self.assertIn(dict(start=at,end=at+1,tokenType='type-parameter'),spans);at=source.rindex('other');self.assertIn(dict(start=at,end=at+5,tokenType='parameter'),spans)
    def test_case_pattern_binding_is_scoped_to_its_case(self):
        source='def f(n: Int) = value match { case n: Int => n; case _ => n }';spans=label(source=source)['spans'];at=source.rindex('n }');self.assertIn(dict(start=at,end=at+1,tokenType='parameter'),spans)
        self.assertNotIn('declaration',next(x for x in spans if x['start']==at).get('modifiers',[]))
    def test_case_class_and_explicit_constructor_properties(self):
        source='case class Pair(left: Int, right: Int)';spans=label(source=source)['spans']
        self.assertTrue(all(x['tokenType']=='property' for x in spans if x.get('modifiers') and source[x['start']:x['end']] in {'left','right'}))
    def test_local_type_constructor_has_no_capitalization_heuristic(self):
        source='class Box; val x = Box(); val y = Unknown()';spans=label(source=source)['spans'];at=source.index('Box()');self.assertIn(dict(start=at,end=at+3,tokenType='constructor'),spans)
        at=source.index('Unknown()');self.assertIn(dict(start=at,end=at+7,tokenType='function'),spans)
    def test_interpolated_fragments_cover_parser_omitted_text_and_quotes(self):
        source='def f(name: String) = s"""🌌 raw $name\r\n// ${name.trim}"""';result=label(source=source)
        encode(dict(source=source,documentKind='scala',result=result,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
        self.assertEqual(result['spans'][-1]['end'],len(source.encode('utf-16-le'))//2)
    def test_plain_strings_are_not_interpolated(self):
        source='"""$name ${code} // text"""';self.assertEqual(label(source=source)['spans'],[dict(start=0,end=len(source),tokenType='string')])
    def test_scala2_braces_and_scala3_indentation_parse_without_sdk(self):
        for source in ['object A { def f(x: Int) = x + 1 }','object A:\n  def f(x: Int) =\n    if x > 0 then x else 0\n']:
            self.assertIn('functions',label(source=source)['features'])
    def test_using_givens_and_extensions_preserve_names(self):
        source='given limit: Int = 2\nextension (s: String)\n  def repeat(using n: Int) = s * n\n';spans=label(source=source)['spans'];at=source.rindex('n\n');self.assertIn(dict(start=at,end=at+1,tokenType='parameter'),spans)
    def test_unicode_crlf_comments_keep_original_offsets(self):
        source='// 🌌\r\nval 名 = "星"\r\n';result=label(source=source);encode(dict(source=source,documentKind='scala',result=result,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_invalid_source_fails_closed(self):
        for source in ['def f(', 'class {', '\0']:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):label(source=source)
if __name__=='__main__':unittest.main()
