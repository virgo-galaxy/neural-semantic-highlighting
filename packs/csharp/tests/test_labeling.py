import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from packs.csharp.labeling.label import label
from training.shared.encoding import Schema, encode
from training.shared.golden import unmark

ROOT = Path(__file__).parents[1]


class CSharpTeacherTests(unittest.TestCase):
    def encode(self, source, result):
        return encode({'source': source, 'documentKind': 'csharp', 'result': result,
                       'contentHash': hashlib.sha256(source.encode()).hexdigest()}, Schema.load(ROOT / 'schema.json'))

    def test_independent_golden_and_original_coordinates(self):
        for case in json.loads((ROOT / 'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                expected = unmark(case['markedSource']); actual = label(source=expected['source'])
                self.assertEqual(actual['spans'], expected['spans'])
                self.encode(expected['source'], actual)

    def test_modern_constructs_and_opaque_strings(self):
        source = '''using System.Linq;
record User(string Name, int Age);
class Users {
  List<User> users = [];
  public required string Title { get; init; }
  public object Run(object input) {
    int[] selected = [1, 2, 3];
    var query = from user in users where user.Age > 18 select user.Name;
    var names = users.Select(user => user.Name);
    var message = input switch { User(var name, > 0) => name, _ => "none" };
    string json = $$"""{ "name": "{{message}}" }""";
    return json;
  }
}'''
        result = label(source=source)
        self.assertTrue({'generics', 'records', 'properties', 'lambdas', 'linq', 'patterns', 'raw-strings', 'collection-expressions'} <= set(result['features']))
        strings = [source[s['start']:s['end']] for s in result['spans'] if s['tokenType'] == 'string']
        self.assertIn('$$"""{ "name": "{{message}}" }"""', strings)
        self.encode(source, result)

    def test_binding_shadowing_and_named_arguments(self):
        source = 'class A { int value; void Set(int value) { this.value = value; Call(count: value); } void Call(int count) {} }'
        result = label(source=source)
        pairs = [(source[s['start']:s['end']], s['tokenType'], s.get('modifiers', [])) for s in result['spans']]
        self.assertIn(('value', 'property', ['declaration']), pairs)
        self.assertIn(('value', 'property', []), pairs)
        self.assertIn(('value', 'parameter', []), pairs)
        self.assertIn(('count', 'parameter', []), pairs)

    def test_invalid_and_unsupported_source_is_quarantined(self):
        for source in ['class A { string x = "unfinished; }', 'class A { void F( }', '#r "unknown.dll"\n', 'class {']:
            with self.subTest(source=source), self.assertRaises(ValueError): label(source=source)

    def test_source_is_never_executed_or_resolved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'must-not-exist'
            source = 'using Missing.Project; [Unknown] class Test { static Test() { System.IO.File.WriteAllText("' + str(path) + '", "bad"); } }'
            self.assertTrue(label(source=source)['spans']); self.assertFalse(path.exists())

    def test_utf8_bom_is_preserved_and_supervised(self):
        source = '\ufeff// Original Windows file\r\nclass Item {}\r\n'
        result = label(source=source)
        self.assertEqual(result['spans'][0], {'start': 0, 'end': 1, 'tokenType': 'punctuation'})
        self.encode(source, result)

    def test_empty_and_input_contracts(self):
        self.assertEqual(label(source='')['spans'], [])
        for kwargs in [{'document_kind': 'razor'}, {'profile': 'preview'}]:
            with self.assertRaises(ValueError): label(source='class A {}', **kwargs)
        with self.assertRaises(ValueError): label(source='\0')


if __name__ == '__main__': unittest.main()
