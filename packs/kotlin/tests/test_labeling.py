import hashlib,json,unittest
from pathlib import Path
from packs.kotlin.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]

class KotlinTeacherTests(unittest.TestCase):
    def test_independent_marked_golden_original_utf16(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);r=label(source=gold['source'],profile=case['profile'])
                self.assertEqual(r['spans'],gold['spans'])
                if gold['source']:encode(dict(source=gold['source'],documentKind='kotlin',result=r,contentHash=hashlib.sha256(gold['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_block_shadowing_preserves_outer_parameter(self):
        s='fun f(value: Int) { run { val value = 1; println(value) }; println(value) }';r=label(source=s)['spans']
        at=s.index('value)');self.assertIn(dict(start=at,end=at+5,tokenType='variable'),r)
        at=s.rindex('value)');self.assertIn(dict(start=at,end=at+5,tokenType='parameter'),r)
    def test_generic_constructor_property_and_member_scope(self):
        s='class Box<T>(val value: T) { fun get(): T = value }';r=label(source=s)['spans'];at=s.rindex('value')
        self.assertIn(dict(start=at,end=at+5,tokenType='property'),r)
        at=s.index('get');self.assertIn(dict(start=at,end=at+3,tokenType='method',modifiers=['declaration']),r)
    def test_constructor_input_is_visible_to_initializers_not_methods(self):
        s='class Box(input: Int) { val value = input; fun bad() = input }';r=label(source=s)['spans']
        at=s.index('input;');self.assertIn(dict(start=at,end=at+5,tokenType='parameter'),r)
        at=s.rindex('input');self.assertIn(dict(start=at,end=at+5,tokenType='variable'),r)
    def test_initializer_locals_are_not_members(self):
        s='class Box { init {\nval local = 1\nfun nested() = local\nprintln(nested())\n} }';r=label(source=s)['spans']
        at=s.index('local');self.assertIn(dict(start=at,end=at+5,tokenType='variable',modifiers=['declaration']),r)
        at=s.index('nested');self.assertIn(dict(start=at,end=at+6,tokenType='function',modifiers=['declaration']),r)
    def test_lambda_it_and_explicit_parameter_do_not_leak(self):
        s='val result = listOf(1).map { it + 1 }; println(it)';r=label(source=s,profile='kotlin-script')['spans']
        at=s.index('it +');self.assertIn(dict(start=at,end=at+2,tokenType='parameter'),r)
        at=s.rindex('it)');self.assertIn(dict(start=at,end=at+2,tokenType='variable'),r)
    def test_function_type_label_does_not_bind_function_body(self):
        s='fun f(block: (item: Int) -> Int) = item';at=s.rindex('item')
        self.assertIn(dict(start=at,end=at+4,tokenType='variable'),label(source=s)['spans'])
    def test_raw_and_multidollar_templates_keep_original_boundaries(self):
        s='fun f(name: String) = $$"""$literal $$name $${name.length}"""';r=label(source=s)
        at=s.index('$$name')+2;self.assertIn(dict(start=at,end=at+4,tokenType='parameter'),r['spans'])
        self.assertIn('interpolation',r['features'])
        self.assertTrue(any(x['tokenType']=='string' and '$literal' in s[x['start']:x['end']] for x in r['spans']))
    def test_crlf_bom_and_astral_text_roundtrip(self):
        s='\ufeffval title = "星空 🌌"\r\nprintln(title)\r\n';r=label(source=s,profile='kotlin-script')
        self.assertIn(dict(start=0,end=1,tokenType='punctuation'),r['spans'])
        encode(dict(source=s,documentKind='kotlin',result=r,contentHash=hashlib.sha256(s.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_accessor_field_and_value_are_scoped(self):
        s='class Box { var number = 0; set(value) { field = value }; fun other() = field }';r=label(source=s)['spans']
        at=s.index('field =');self.assertIn(dict(start=at,end=at+5,tokenType='property'),r)
        at=s.rindex('field');self.assertIn(dict(start=at,end=at+5,tokenType='variable'),r)
    def test_current_syntax_and_compose_need_no_android_or_plugins(self):
        for s in ['context(logger: Logger) fun f() = logger.log("ready")','@Composable fun Panel() { Text(text = "Hi") }','@JvmInline value class Id(val value: String)','data object Empty','sealed interface Event']:
            self.assertTrue(label(source=s)['spans'])
    def test_scripts_are_parsed_without_execution_or_dependency_resolution(self):
        s='@file:DependsOn("missing:artifact:1")\nerror("must never run")\njava.io.File("/tmp/nsh-must-not-write").writeText("never")'
        self.assertTrue(label(source=s,profile='kotlin-script')['spans'])
    def test_invalid_source_fails_closed(self):
        for s in ['fun bad( {','val x = "unterminated','val x=1\0']:
            with self.assertRaises(ValueError):label(source=s)
        with self.assertRaises(ValueError):label(source='',profile='java')
        self.assertEqual(label(source='')['spans'],[])

if __name__=='__main__':unittest.main()
