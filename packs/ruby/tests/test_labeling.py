import hashlib,json,unittest
from pathlib import Path
from packs.ruby.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class RubyTeacherTests(unittest.TestCase):
    def test_independent_marked_golden_original_utf16(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);result=label(source=gold['source']);self.assertEqual(result['spans'],gold['spans'])
                if gold['source']:encode(dict(source=gold['source'],documentKind='ruby',result=result,contentHash=hashlib.sha256(gold['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_method_does_not_capture_top_level_local(self):
        source='value = 1; def f; value; end';s=label(source=source)['spans'];at=source.rindex('value');self.assertIn(dict(start=at,end=at+5,tokenType='function'),s)
    def test_blocks_capture_locals_and_shadow_parameters(self):
        source='value = 1; [2].map { |value| value }; value';s=label(source=source)['spans'];at=source.index('value }');self.assertIn(dict(start=at,end=at+5,tokenType='parameter'),s);at=source.rindex('value');self.assertIn(dict(start=at,end=at+5,tokenType='variable'),s)
    def test_block_local_does_not_escape(self):
        source='[1].each { |n; scratch| scratch = n }; scratch';s=label(source=source)['spans'];at=source.rindex('scratch');self.assertIn(dict(start=at,end=at+7,tokenType='function'),s)
    def test_heredoc_interpolation_preserves_method_parameter_scope(self):
        source='def f(name)\n text = <<~DOC\nHi #{name}!\nDOC\nend\n';s=label(source=source)['spans'];at=source.index('#{name}')+2;self.assertIn(dict(start=at,end=at+4,tokenType='parameter'),s)
    def test_quoted_heredoc_is_not_interpolated(self):
        source="text = <<'DOC'\n#{never_executed}\nDOC\n";s=label(source=source)['spans'];self.assertEqual([x['tokenType'] for x in s],['variable','operator','string'])
    def test_percent_arrays_and_regex_keep_expression_roles(self):
        source='def f(name) = %W[one #{name}]';s=label(source=source)['spans'];at=source.index('#{name}')+2;self.assertIn(dict(start=at,end=at+4,tokenType='parameter'),s)
    def test_pattern_shorthand_binds_local_without_rescanning(self):
        source='case value; in {name:}; name; end';s=label(source=source)['spans'];at=source.rindex('name');self.assertIn(dict(start=at,end=at+4,tokenType='variable'),s)
    def test_constant_role_comes_from_cst_not_capitalization_rules(self):
        source='class Box; end; Box; Unknown';s=label(source=source)['spans'];at=source.index('Box;',10);self.assertIn(dict(start=at,end=at+3,tokenType='type'),s);at=source.index('Unknown');self.assertIn(dict(start=at,end=at+7,tokenType='constant'),s)
    def test_named_and_numbered_block_parameters(self):
        source='[1].map { _1 + 2 }';s=label(source=source)['spans'];at=source.index('_1');self.assertIn(dict(start=at,end=at+2,tokenType='parameter'),s)
    def test_unicode_crlf_original_heredoc_offsets_encode(self):
        source='def f(name)\r\n text = <<~DOC\r\n星 🌌 #{name}\r\nDOC\r\nend\r\n';result=label(source=source);encode(dict(source=source,documentKind='ruby',result=result,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_explicit_line_continuation_is_restored_only_in_parser_gaps(self):
        source='text = "one" '+chr(92)+'\r\n  "two"\r\n';result=label(source=source);at=source.index(chr(92));self.assertIn(dict(start=at,end=at+1,tokenType='punctuation'),result['spans'])
        encode(dict(source=source,documentKind='ruby',result=result,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
        literal='"one'+chr(92)+'\n two"';self.assertEqual([s['tokenType'] for s in label(source=literal)['spans']],['string'])
    def test_invalid_source_fails_closed(self):
        for source in ['def f(', 'text = <<~DOC\nmissing', '\0']:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):label(source=source)
if __name__=='__main__':unittest.main()
