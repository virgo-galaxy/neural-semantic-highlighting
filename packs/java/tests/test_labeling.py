import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from packs.java.labeling.label import label
from training.shared.encoding import Schema, encode
from training.shared.golden import unmark

ROOT = Path(__file__).parents[1]


class JavaTeacherTests(unittest.TestCase):
    def test_independent_golden_and_original_coordinates(self):
        for case in json.loads((ROOT / 'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                expected = unmark(case['markedSource'])
                result = label(source=expected['source'])
                self.assertEqual(result['spans'], expected['spans'])
                encode({'source': expected['source'], 'documentKind': 'java', 'result': result,
                        'contentHash': hashlib.sha256(expected['source'].encode()).hexdigest()}, Schema.load(ROOT / 'schema.json'))

    def test_modern_syntax_and_contextual_keywords(self):
        source = '''sealed interface Event permits Note {}
record Note(String text) implements Event {}
class Display {
  String show(Event item) {
    return switch (item) {
      case Note(var text) when !text.isBlank() -> text;
      default -> { yield "empty"; }
    };
  }
  String template = """
      <section>record is content, not syntax</section>
      """;
}'''
        result = label(source=source)
        self.assertTrue({'sealed', 'records', 'pattern-matching', 'switch-expressions', 'text-blocks'} <= set(result['features']))
        keywords = {source[s['start']:s['end']] for s in result['spans'] if s['tokenType'] == 'keyword'}
        self.assertTrue({'sealed', 'permits', 'record', 'var', 'when', 'yield'} <= keywords)
        strings = [source[s['start']:s['end']] for s in result['spans'] if s['tokenType'] == 'string']
        self.assertEqual(len(strings), 2)
        self.assertTrue(strings[-1].startswith('"""'))

    def test_forward_members_shadowing_and_nested_bounds(self):
        source = 'class Box<T extends Comparable<T>> { int get(int count) { int result = count; return result + size; } int size; }'
        result = label(source=source)
        matches = [(source[s['start']:s['end']], s['tokenType'], s.get('modifiers', [])) for s in result['spans']]
        self.assertEqual(sum(text == 'T' and mods == ['declaration'] for text, role, mods in matches), 1)
        self.assertIn(('count', 'parameter', []), matches)
        self.assertIn(('size', 'property', []), matches)

    def test_parse_errors_and_preview_are_quarantined(self):
        for source in ['class A { String x = "unfinished; }', 'class {', 'class A { void f( }', 'class A { String x = STR."hello \\{name}"; }']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                label(source=source)

    def test_source_and_annotation_processors_are_never_run(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / 'must-not-exist'
            source = 'import missing.Dependency; @Unknown class Probe { static { new java.io.File("' + str(sentinel) + '").createNewFile(); } }'
            self.assertTrue(label(source=source)['spans'])
            self.assertFalse(sentinel.exists())

    def test_scope_and_input_contracts(self):
        for kwargs in [{'document_kind': 'javascript'}, {'profile': 'preview'}]:
            with self.assertRaises(ValueError): label(source='class A {}', **kwargs)
        with self.assertRaises(ValueError): label(source='\0')
        self.assertEqual(label(source='')['spans'], [])


if __name__ == '__main__':
    unittest.main()
