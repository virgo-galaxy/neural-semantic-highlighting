import hashlib,json,unittest
from pathlib import Path
from packs.toml.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class TomlTeacherTests(unittest.TestCase):
 def encode(self,source):
  result=label(source=source)
  if source:encode(dict(source=source,documentKind='toml',result=result,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
  return result
 def test_independent_marked_original_utf16(self):
  for c in json.loads((ROOT/'fixtures/golden.json').read_text()):
   with self.subTest(case=c['id']):
    g=unmark(c['markedSource']);self.assertEqual(self.encode(g['source'])['spans'],g['spans'])
 def test_header_and_assignment_segments_have_different_roles(self):
  spans=self.encode('[a."b.c"]\na.b=1')['spans'];self.assertEqual(sum(s['tokenType']=='namespace'for s in spans),2);self.assertEqual(sum(s['tokenType']=='property'for s in spans),2)
 def test_quoted_boolean_and_dates_stay_string(self):
  spans=self.encode('xs=["true",\'2026-11-15\',"12"]')['spans'];self.assertEqual(sum(s['tokenType']=='string'for s in spans),3)
 def test_dates_keep_original_range_including_space_and_offset(self):
  source='time = 1979-05-27 07:32:00.123-08:00';spans=self.encode(source)['spans'];s=spans[-1];self.assertEqual(source[s['start']:s['end']],'1979-05-27 07:32:00.123-08:00');self.assertEqual(s['tokenType'],'number')
 def test_multiline_literal_is_opaque_source(self):
  source='text = """\r\n# not comment\r\n{\"x\": true}\r\n🌌\r\n"""';spans=self.encode(source)['spans'];self.assertEqual(len(spans),3);self.assertEqual(spans[-1]['tokenType'],'string');self.assertEqual(spans[-1]['end'],len(source.encode('utf-16-le'))//2)
 def test_11_inline_table_comments_newlines_and_trailing_comma(self):
  spans=self.encode('row={\n x=1, # note\n y=false,\n}\n')['spans'];self.assertEqual(sum(s['tokenType']=='comment'for s in spans),1)
 def test_11_new_escapes_and_optional_seconds(self):
  for source in ['s="\\e\\xE9"','d=07:32','d=1979-05-27T07:32Z']:
   self.encode(source)
 def test_integer_separators_signs_radices_and_special_float(self):
  spans=self.encode('n=[-1_000,0xff,0o77,0b101,+nan,-inf]')['spans'];self.assertEqual(sum(s['tokenType']=='number'for s in spans),6)
 def test_unicode_crlf_keys_and_comment_original_offsets(self):
  self.encode('"标题🌌"="星空" # note\r\n')
 def test_duplicate_redefined_and_invalid_source_fails_closed(self):
  for source in ['x=1\nx=2','a=1\n[a]','x="bad\\q"','x=[1,','x=null','\ufeffx=1','x=01','x=1\0']:
   with self.subTest(source=source):
    with self.assertRaises(ValueError):self.encode(source)
 def test_arrays_of_tables_do_not_expand_or_execute_configuration(self):
  spans=self.encode('[[tasks]]\nrun="$(touch /not/run)"\n[[tasks]]\nrun="echo done"')['spans'];self.assertEqual(sum(s['tokenType']=='namespace'for s in spans),2);self.assertTrue(all('modifiers'not in s for s in spans))
 def test_editor_empty_and_profile_guard(self):
  self.assertEqual(label(source=' \r\n')['spans'],[])
  with self.assertRaises(ValueError):label(source='x=1',profile='yaml')
if __name__=='__main__':unittest.main()
