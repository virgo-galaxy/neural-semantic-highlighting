import hashlib,json,unittest
from pathlib import Path
from packs.dotenv.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class DotenvTeacherTests(unittest.TestCase):
 def encode(self,source):
  result=label(source=source)
  if source:encode(dict(source=source,documentKind='dotenv',result=result,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
  return result
 def test_independent_marked_original_ranges(self):
  for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
   with self.subTest(case=case['id']):
    g=unmark(case['markedSource']);self.assertEqual(self.encode(g['source'])['spans'],g['spans'])
 def test_all_values_are_strings_and_bindings_declarations(self):
  spans=self.encode('COUNT=42\nENABLED=true\nVALUE=null')['spans'];self.assertEqual([s['tokenType']for s in spans],['variable','punctuation','string']*3);self.assertTrue(all(s.get('modifiers')==['declaration']for s in spans if s['tokenType']=='variable'))
 def test_export_keyword_and_export_named_key_differ(self):
  spans=self.encode('export APP=preview\nexport =literal')['spans'];self.assertEqual(sum(s['tokenType']=='keyword'for s in spans),1)
 def test_hash_comments_depend_on_quote_context(self):
  spans=self.encode('A=raw# comment\nB="a#b" # note\nC= # empty')['spans'];self.assertEqual(sum(s['tokenType']=='comment'for s in spans),3)
 def test_multiline_value_keeps_embedded_assignments_and_hashes(self):
  source='TEXT="first\nA=true\n# data\nlast"\nREADY=yes';spans=self.encode(source)['spans'];self.assertEqual(len(spans),6);self.assertEqual(spans[2]['tokenType'],'string');self.assertEqual(source[spans[2]['start']:spans[2]['end']],'"first\nA=true\n# data\nlast"')
 def test_double_quote_newline_escapes_do_not_rewrite_source(self):
  source='TEXT="first\\nsecond\\r"';self.assertEqual(self.encode(source)['spans'][-1]['end'],len(source))
 def test_references_and_commands_are_opaque_strings(self):
  for value in ['${HOME:-./cache}','$PORT','$(touch /not/run)','`echo not executed`','"${HOST}/$PORT"']:
   self.assertEqual(self.encode('VALUE='+value)['spans'][-1]['tokenType'],'string')
 def test_duplicate_and_case_sensitive_keys_keep_every_declaration(self):
  spans=self.encode('X=1\nX=2\nx=3')['spans'];self.assertEqual(sum(s['tokenType']=='variable'for s in spans),3)
 def test_empty_values_do_not_invent_tokens(self):
  spans=self.encode('EMPTY=\nNEXT= # note\nLAST=""')['spans'];self.assertEqual(sum(s['tokenType']=='string'for s in spans),1)
 def test_bom_unicode_and_crlf_keep_original_utf16(self):
  source='\ufeffTEXT="星空 🌌\r\n👩🏽‍💻"\r\n';spans=self.encode(source)['spans'];self.assertEqual(spans[0],dict(start=0,end=1,tokenType='punctuation'));self.assertEqual(spans[-1]['end'],len(source.rstrip('\r\n').encode('utf-16-le'))//2)
 def test_invalid_or_uncovered_syntax_fails_closed(self):
  for source in ['A="unfinished','KEY','NAME: value','1_NAME=value','A-B=value','A="value" trailing','A=1\0','A=1\rB=2','__proto__=value']:
   with self.subTest(source=source):
    with self.assertRaises(ValueError):self.encode(source)
 def test_empty_editor_input_and_kind_profile_guard(self):
  self.assertEqual(label(source=' \r\n')['spans'],[])
  with self.assertRaises(ValueError):label(source='X=1',profile='ini')
if __name__=='__main__':unittest.main()
