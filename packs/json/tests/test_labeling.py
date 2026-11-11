import hashlib,json,unittest
from pathlib import Path
from packs.json.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class JsonTeacherTests(unittest.TestCase):
 def encode(self,source,kind='json'):
  result=label(source=source,document_kind=kind)
  if source:encode(dict(source=source,documentKind=kind,result=result,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
  return result
 def test_independent_marked_golden_original_utf16(self):
  for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
   with self.subTest(case=case['id']):
    gold=unmark(case['markedSource']);self.assertEqual(self.encode(gold['source'],case['documentKind'])['spans'],gold['spans'])
 def test_keys_and_equal_value_text_have_distinct_roles(self):
  s=self.encode('{"same":"same"}')['spans'];self.assertEqual(s[1]['tokenType'],'property');self.assertEqual(s[3]['tokenType'],'string');self.assertTrue(all('modifiers' not in x for x in s))
 def test_strict_json_rejects_comments_and_trailing_commas(self):
  for source in ['// note\n{}','{/*note*/"x":1}','{"x":1,}','[1,]']:
   with self.subTest(source=source):
    with self.assertRaises(ValueError):self.encode(source)
    self.encode(source,'jsonc')
 def test_jsonc_comment_ranges_exclude_original_crlf(self):
  s=self.encode('// 🌌\r\n{}','jsonc')['spans'];self.assertEqual(s[0],dict(start=0,end=5,tokenType='comment'));self.assertEqual(s[1]['start'],7)
 def test_comment_markers_inside_strings_remain_strings(self):
  s=self.encode('{"url":"https://example.test/a/*x*/?q=//","code":"{\\"x\\":1}"}','jsonc')['spans'];self.assertEqual(sum(x['tokenType']=='string' for x in s),2);self.assertFalse(any(x['tokenType']=='comment' for x in s))
 def test_parser_recovery_never_accepts_invalid_structure(self):
  for source in ['{"x":}','{"x" 1}','[1 2]','true false','{','[','{"x":1,,}','[,]']:
   for kind in ['json','jsonc']:
    with self.subTest(source=source,kind=kind):
     with self.assertRaises(ValueError):self.encode(source,kind)
 def test_non_json5_contract(self):
  for source in ["{'x':1}",'{x:1}','NaN','Infinity','undefined','+1','0x10','01','-.5','1.','1e','{"x":/*a*/NaN}']:
   with self.subTest(source=source):
    with self.assertRaises(ValueError):self.encode(source,'jsonc')
 def test_incomplete_strings_comments_and_bad_escape_fail_closed(self):
  for source in ['"unfinished','"bad\\x20"','"raw\nline"','/* unfinished','{"x":"bad\\u12"}','"a\tb"','\0']:
   with self.subTest(source=source):
    with self.assertRaises(ValueError):self.encode(source,'jsonc')
 def test_duplicate_and_prototype_names_remain_original_data(self):
  source='{"__proto__":1,"x":2,"x":3,"constructor":4}';s=self.encode(source)['spans'];self.assertEqual(sum(x['tokenType']=='property' for x in s),4);self.assertEqual(sum(x['tokenType']=='number' for x in s),4)
 def test_original_large_numbers_and_negative_zero_keep_one_span(self):
  for source in ['-0','123456789012345678901234567890','1e400','-1.5E-12']:
   self.assertEqual(self.encode(source)['spans'],[dict(start=0,end=len(source),tokenType='number')])
 def test_unicode_combining_characters_and_crlf_original_offsets(self):
  self.encode('{\r\n"é 🌌":"👩🏽‍💻 星空",\r\n"escaped":"\\uD83C\\uDF0C"\r\n}')
 def test_json_whitespace_does_not_expand_to_javascript_whitespace(self):
  for source in ['\u00a0{}','{}\v','{}\f','\ufeff{}']:
   with self.subTest(source=source):
    with self.assertRaises(ValueError):self.encode(source,'jsonc')
 def test_profile_kind_must_agree_and_empty_editor_input_is_supported(self):
  with self.assertRaises(ValueError):label(source='{}',document_kind='json',profile='jsonc')
  for kind in ['json','jsonc']:self.assertEqual(label(source=' \t\r\n',document_kind=kind)['spans'],[])
if __name__=='__main__':unittest.main()
