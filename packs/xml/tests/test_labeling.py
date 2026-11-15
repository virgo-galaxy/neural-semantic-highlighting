import hashlib,json,unittest
from pathlib import Path
from packs.xml.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class XmlTeacherTests(unittest.TestCase):
 def check(self,source,kind='xml'):
  r=label(source=source,document_kind=kind)
  if source:encode(dict(source=source,documentKind=kind,result=r,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
  return r
 def test_independently_marked_original_ranges(self):
  for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
   with self.subTest(case=case['id']):
    g=unmark(case['markedSource']);self.assertEqual(self.check(g['source'],case['documentKind'])['spans'],g['spans'])
 def test_counterpart_curriculum_uses_one_source_family_identity(self):
  rows=json.loads((ROOT/'dataset/sources.json').read_text())['sources']
  for directory in ['curriculum-v1','mixed-v1']:
   sources=[x for x in rows if x['path'].endswith('/'+directory)]
   self.assertEqual({x['profile']for x in sources},{'xml','svg'})
   self.assertEqual(len({(x['id'],x['groupBy'])for x in sources}),1)
 def test_case_sensitive_matching(self):
  with self.assertRaises(ValueError):self.check('<Name></name>')
 def test_xml_has_no_html_void_or_unquoted_attribute_rules(self):
  for src in ['<br>','<input disabled/>','<a href=link/>','<a>&nbsp;</a>','<a><b></a>']:
   with self.subTest(source=src),self.assertRaises(ValueError):self.check(src)
 def test_namespace_bindings_and_duplicate_expanded_attributes(self):
  for src in ['<m:r/>','<r xmlns:a="urn:x" xmlns:b="urn:x" a:key="1" b:key="2"/>','<r key="1" key="2"/>']:
   with self.subTest(source=src),self.assertRaises(ValueError):self.check(src)
 def test_entities_preserve_original_spelling(self):
  source='<r>&amp;&#65;&#x1F30C;</r>';r=self.check(source);self.assertEqual([source[s['start']:s['end']]for s in r['spans']if s['tokenType']=='entity'],['&amp;','&#65;','&#x1F30C;'])
 def test_cdata_is_one_opaque_string(self):
  r=self.check('<r><![CDATA[<a>&amp; x < 3]]></r>');self.assertEqual([s['tokenType']for s in r['spans']],['punctuation','tag','punctuation','string','punctuation','tag','punctuation'])
 def test_external_doctype_is_not_fetched(self):
  r=self.check('<!DOCTYPE r SYSTEM "file:///does-not-exist/nsh.dtd"><r/>');self.assertEqual(r['spans'][0]['tokenType'],'keyword')
 def test_custom_entity_declarations_fail_without_expansion(self):
  for src in ['<!DOCTYPE r [<!ENTITY a "secret">]><r>&a;</r>','<!DOCTYPE r [<!ENTITY a SYSTEM "file:///etc/passwd">]><r>&a;</r>','<!DOCTYPE r [<!ENTITY % a SYSTEM "https://example.test/x"> %a;]><r/>']:
   with self.subTest(source=src),self.assertRaises(ValueError):self.check(src)
 def test_unicode_bom_crlf_use_original_utf16(self):
  src='\ufeff<标题>🌌\r\n</标题>\r\n';r=self.check(src);self.assertEqual(r['spans'][0],dict(start=0,end=1,tokenType='punctuation'));self.assertEqual(r['spans'][-1]['end'],len(src.rstrip('\r\n').encode('utf-16-le'))//2)
 def test_processing_instruction_and_doctype_are_opaque(self):
  r=self.check('<?xml-stylesheet href="x.xsl"?><!DOCTYPE r [<!ELEMENT r ANY>]><r/>');self.assertEqual([s['tokenType']for s in r['spans'][:2]],['keyword','keyword'])
 def test_svg_and_xml_share_roles_without_path_or_css_parsing(self):
  src='<svg><path d="M1 2L3 4" style="fill: red"/></svg>';self.assertEqual(self.check(src,'xml'),self.check(src,'svg'));self.assertEqual(sum(s['tokenType']=='string'for s in self.check(src)['spans']),2)
 def test_invalid_and_incomplete_source_fails_closed(self):
  for src in ['<r><!-- unclosed</r>','<r><![CDATA[a</r>','<r>&unknown;</r>','<?xml version="1.1"?><r/>','<r>\0</r>','<r a="unfinished/>','<r/>trailing','<r/><r/>']:
   with self.subTest(source=src),self.assertRaises(ValueError):self.check(src)
 def test_empty_comment_editor_input_and_kind_guard(self):
  self.assertEqual(self.check(' \r\n')['spans'],[]);self.assertEqual(len(self.check('<!-- note -->')['spans']),1)
  with self.assertRaises(ValueError):label(source='<r/>',document_kind='html')
  with self.assertRaises(ValueError):label(source='<r/>',document_kind='svg',profile='xml')
if __name__=='__main__':unittest.main()
