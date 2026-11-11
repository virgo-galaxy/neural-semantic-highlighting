import hashlib,json,unittest
from pathlib import Path
from packs.swift.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT = Path(__file__).parents[1]

class SwiftTeacherTests(unittest.TestCase):
    def test_independent_marked_golden_original_utf16(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold = unmark(case['markedSource']); result = label(source=gold['source'])
                self.assertEqual(result['spans'],gold['spans'])
                if gold['source']: encode(dict(source=gold['source'],documentKind='swift',result=result,contentHash=hashlib.sha256(gold['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_block_shadowing_and_parameter_labels(self):
        source = 'func f(to value: Int) { do { let value = 1; print(value) }; print(value) }'
        spans = label(source=source)['spans']
        at=source.index('value)'); self.assertIn(dict(start=at,end=at+5,tokenType='variable'),spans)
        at=source.rindex('value)'); self.assertIn(dict(start=at,end=at+5,tokenType='parameter'),spans)
        at=source.index('to '); self.assertIn(dict(start=at,end=at+2,tokenType='parameter'),spans)
    def test_local_functions_do_not_become_methods(self):
        source='struct A { func outer() { func nested() {} ; nested() } }'
        spans=label(source=source)['spans']; at=source.index('nested')
        self.assertIn(dict(start=at,end=at+6,tokenType='function',modifiers=['declaration']),spans)
    def test_generic_and_closure_parameters_do_not_leak(self):
        source='func keep<T>(_ value: T) -> T { value }; let f = { item in item }; print(item)'
        spans=label(source=source)['spans']; at=source.rindex('item')
        self.assertIn(dict(start=at,end=at+4,tokenType='variable'),spans)
        self.assertIn('generics',label(source=source)['features'])
    def test_raw_strings_regex_and_nested_comments_keep_original_boundaries(self):
        source='let text = #"\\(fake) // no comment"#; let rx = #/[a-z] // literal/#; /* a /* b */ c */'
        result=label(source=source)
        self.assertEqual(sum(s['tokenType']=='string' for s in result['spans']),2)
        self.assertEqual(sum(s['tokenType']=='comment' for s in result['spans']),1)
        self.assertNotIn('interpolation',result['features'])
    def test_raw_interpolation_keeps_code_roles(self):
        source='func f(_ value: Int) -> String { #"Hi \\#(value + 1)"# }'
        spans=label(source=source)['spans']; at=source.rindex('value')
        self.assertIn(dict(start=at,end=at+5,tokenType='parameter'),spans)
        self.assertIn('interpolation',label(source=source)['features'])
    def test_imported_calls_do_not_get_capitalization_heuristics(self):
        source='import SwiftUI\nlet content = Text("Hello"); struct Local {}; let item = Local()'
        spans=label(source=source)['spans']; at=source.index('Text')
        self.assertIn(dict(start=at,end=at+4,tokenType='function'),spans)
        at=source.rindex('Local'); self.assertIn(dict(start=at,end=at+5,tokenType='constructor'),spans)
    def test_current_syntax_and_swiftui_do_not_load_project_environment(self):
        for source in ['import MissingPackage\n#UnknownMacro("never executed")','struct Handle: ~Copyable { consuming func close() {} }','enum E: Error { case failed }; func f() throws(E) { throw .failed }','import SwiftUI\nstruct Panel: View { @State var count = 0; var body: some View { Button("Add") { count += 1 } } }']:
            self.assertTrue(label(source=source)['spans'])
    def test_multiline_continuations_preserve_non_whitespace_trivia(self):
        for source in ['let text = """\nHello \\(name) \\\nworld\n"""', 'let text = #"""\nHello \\#\nworld\n"""#']:
            result = label(source=source)
            self.assertTrue(result["spans"])
            self.assertNotIn("comments", result["features"])

    def test_type_labels_and_enum_payload_labels_are_parameters(self):
        for source,name in [("typealias Handler = (_ count: Int) -> String", "count"),("enum Outcome { case ready(value: Int) }", "value")]:
            at=source.index(name)
            self.assertIn(dict(start=at,end=at+len(name),tokenType="parameter"),label(source=source)["spans"])

    def test_implicit_accessor_and_catch_parameter_scopes(self):
        for source,name in [("struct Box { var value: Int { get { 1 } set { print(newValue) } } }", "newValue"),("func f() { do {} catch { print(error) }; print(error) }", "error")]:
            at=source.index(name)
            self.assertIn(dict(start=at,end=at+len(name),tokenType="parameter"),label(source=source)["spans"])

    def test_invalid_source_fails_closed(self):
        for source in ['func broken( {','let text = "unfinished','func f() {\0}']:
            with self.assertRaises(ValueError): label(source=source)
        with self.assertRaises(ValueError): label(source='',document_kind='swiftui')
        self.assertEqual(label(source='')['spans'],[])

if __name__=='__main__': unittest.main()
