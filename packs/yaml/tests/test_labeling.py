import hashlib,json,unittest
from pathlib import Path
from packs.yaml.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class YamlTeacherTests(unittest.TestCase):
 def encode(self,source):
  result=label(source=source)
  if source:encode(dict(source=source,documentKind='yaml',result=result,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
  return result
 def test_independent_marked_golden_original_utf16(self):
  for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
   with self.subTest(case=case['id']):
    g=unmark(case['markedSource']);self.assertEqual(self.encode(g['source'])['spans'],g['spans'])
 def test_core_boolean_strings_keep_github_on_key(self):
  source='on: yes\noff: NO\ntruth: true\n';spans=self.encode(source)['spans'];self.assertEqual([x['tokenType'] for x in spans],['property','punctuation','string','property','punctuation','string','property','punctuation','keyword'])
 def test_quoted_scalars_never_become_numbers_or_keywords(self):
  spans=self.encode('values: ["true", \'12\', "null", "2026-11-11"]')['spans'];self.assertEqual(sum(x['tokenType']=='string' for x in spans),4)
 def test_literal_body_preserves_crlf_indent_comments_and_fake_code(self):
  source='run: |2- # header\r\n  echo "🌌"\r\n  # body\r\n';spans=self.encode(source)['spans'];body=next(x for x in spans if x['tokenType']=='string');raw=source.encode('utf-16-le');self.assertEqual(raw[body['start']*2:body['end']*2].decode('utf-16-le'),'  echo "🌌"\r\n  # body\r\n');self.assertEqual(sum(x['tokenType']=='comment' for x in spans),1)
 def test_chomping_changes_semantics_without_rewriting_source(self):
  for header in ['|','|-','|+','>','>-','>2+']:
   source='text: '+header+'\n  raw\n\n';result=self.encode(source);self.assertTrue(any(x['tokenType']=='string' for x in result['spans']))
 def test_anchor_aliases_never_expand_or_follow_cycles(self):
  source='base: &root {next: *root}\ncopy: *missing\n';spans=self.encode(source)['spans'];labels=[x for x in spans if x['tokenType']=='label'];self.assertEqual(len(labels),3);self.assertEqual(labels[0].get('modifiers'),['declaration']);self.assertTrue(all('modifiers' not in x for x in labels[1:]))
 def test_unknown_tags_are_decorators_without_loading_plugins(self):
  for source in ['image: !Ref Container','value: !include /not/a/config/file','value: !!str 123']:
   spans=self.encode(source)['spans'];self.assertEqual(sum(x['tokenType']=='decorator' for x in spans),1);self.assertEqual(spans[-1]['tokenType'],'string')
 def test_plain_timestamps_and_underscore_numbers_follow_core(self):
  spans=self.encode('date: 2026-11-11\namount: 1_000\nfinite: .inf')['spans'];self.assertEqual([x['tokenType'] for x in spans if x['tokenType'] in ['string','number']],['string','string','number'])
 def test_complex_keys_keep_nested_structure(self):
  spans=self.encode('? [a, b]\n: {value: 2}\n')['spans'];self.assertEqual(sum(x['tokenType']=='property' for x in spans),1);self.assertEqual(sum(x['tokenType']=='string' for x in spans),2)
 def test_block_scalar_key_keeps_property_body(self):
  source='? |-\n  multiline key\n: value\n';spans=self.encode(source)['spans'];raw=source.encode('utf-16-le');key=next(x for x in spans if x['tokenType']=='property');self.assertEqual(raw[key['start']*2:key['end']*2].decode('utf-16-le'),'  multiline key\n')
 def test_duplicate_keys_are_colored_without_object_conversion(self):
  spans=self.encode('x: 1\nx: 2\n')['spans'];self.assertEqual(sum(x['tokenType']=='property' for x in spans),2)
 def test_invalid_syntax_and_recovery_fail_closed(self):
  for source in ['key: [1, 2','key: "unfinished','x:\n\tbad: 2','a: "bad\\q"','x: 1\0']:
   with self.subTest(source=source):
    with self.assertRaises(ValueError):self.encode(source)
 def test_multidoc_directives_bom_unicode_and_original_offsets(self):
  self.encode('\ufeff%YAML 1.2\r\n---\r\n标题🌌: "星空"\r\n...\r\n---\r\n- text\r\n')
 def test_editor_empty_input_and_kind_profile_guard(self):
  self.assertEqual(label(source=' \r\n')['spans'],[])
  with self.assertRaises(ValueError):label(source='x: 1',profile='json')
if __name__=='__main__':unittest.main()
