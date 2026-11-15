import hashlib,json,unittest
from pathlib import Path
from packs.ini.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class IniTeacherTests(unittest.TestCase):
 def encode(self,source):
  r=label(source=source)
  if source:encode(dict(source=source,documentKind='ini',result=r,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
  return r
 def test_independent_marked_original_ranges(self):
  for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
   with self.subTest(case=case['id']):
    g=unmark(case['markedSource']);self.assertEqual(self.encode(g['source'])['spans'],g['spans'])
 def test_root_and_duplicate_sections_keys_are_retained(self):
  r=self.encode('x=1\nx=2\n[app]\nx=3\n[app]\ny=4');self.assertEqual(sum(s['tokenType']=='property'for s in r['spans']),4);self.assertEqual(sum(s['tokenType']=='namespace'for s in r['spans']),2)
 def test_section_name_is_one_original_namespace(self):
  source='[remote "origin.with.dot"] # header\nurl=./repo';s=self.encode(source)['spans'][1];self.assertEqual(source[s['start']:s['end']],'remote "origin.with.dot"')
 def test_inline_hash_semicolon_and_quotes_stay_value_data(self):
  source='text="a # value; kept" ; still value';r=self.encode(source);self.assertEqual(r['spans'][-1]['tokenType'],'string');self.assertEqual(sum(s['tokenType']=='comment'for s in r['spans']),0)
 def test_first_delimiter_keeps_url_and_colons_in_value(self):
  r=self.encode('url=https://example.test:8080/a=b#part');self.assertEqual(len(r['spans']),3)
 def test_indented_continuation_has_opaque_physical_line_ranges(self):
  source='items = alpha\n  beta=true\n  # a comment\n\n  gamma\nready=yes';r=self.encode(source);self.assertEqual([s['tokenType']for s in r['spans']],['property','punctuation','string','string','comment','string','property','punctuation','keyword'])
 def test_deeper_indented_header_is_continuation(self):
  r=self.encode('[app]\ntext=first\n  [not a section]\nlast=value');self.assertEqual(sum(s['tokenType']=='namespace'for s in r['spans']),1)
 def test_bool_number_coloring_is_display_only(self):
  r=self.encode('a=YES\nb=0\nc="false"\nd=1.25e+3\ne=30s\nf=null');self.assertEqual([s['tokenType']for s in r['spans']][2::3],['keyword','number','string','number','string','string'])
 def test_interpolation_and_default_names_do_not_load_or_expand(self):
  self.encode('[DEFAULT]\npath=%(missing)s/${ENV}\n[other]\nrun=$(touch /not/run)');self.assertTrue(all('modifiers'not in s for s in label(source='x=true')['spans']))
 def test_bom_unicode_crlf_keep_original_offsets(self):
  r=self.encode('\ufeff[设置🌌]\r\n标题=星空\r\n');self.assertEqual(r['spans'][0],dict(start=0,end=1,tokenType='punctuation'))
 def test_invalid_headers_empty_keys_controls_and_valueless_continuations(self):
  for source in ['[unclosed','[]=1','[a] trailing text','=empty','flag\n  continuation','x=1\0','x=1\ry=2']:
   with self.subTest(source=source):
    with self.assertRaises(ValueError):self.encode(source)
 def test_empty_editor_input_and_kind_profile_guard(self):
  self.assertEqual(label(source=' \r\n')['spans'],[])
  with self.assertRaises(ValueError):label(source='x=1',profile='toml')
if __name__=='__main__':unittest.main()
