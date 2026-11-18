import hashlib,json,unittest
from pathlib import Path
from packs.protobuf.labeling.label import label
from training.shared.golden import unmark
from training.shared.encoding import Schema,encode
ROOT=Path(__file__).parents[1]
class ProtobufTeacherTests(unittest.TestCase):
 def encode(self,s):
  r=label(source=s)
  if s:encode(dict(source=s,documentKind='protobuf',result=r,contentHash=hashlib.sha256(s.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
  return r
 def test_independently_marked_original_ranges(self):
  for c in json.loads((ROOT/'fixtures/golden.json').read_text()):
   with self.subTest(case=c['id']):
    g=unmark(c['markedSource']);self.assertEqual(self.encode(g['source'])['spans'],g['spans'])
 def test_invalid_and_wrong_profile_rejected(self):
  for s in ['message X { string name = ; }','syntax="proto3";\0','message {','option a="unterminated;']:
   with self.subTest(source=s):
    with self.assertRaises(ValueError):self.encode(s)
  with self.assertRaises(ValueError):label(source='',profile='graphql')
 def test_imports_not_loaded_and_values_not_executed(self):
  self.encode('import "does/not/exist.proto"; option command="$(never run)";')
 def test_concatenated_literals_keep_intervening_comment(self):
  r=self.encode('option note="first" /* keep */ "🌌";');self.assertEqual([s['tokenType']for s in r['spans']],['keyword','property','operator','string','comment','string','punctuation'])
 def test_editions_import_option_and_visibility(self):
  self.encode('edition="2024"; import option "options.proto"; local message Hidden {} export enum Public { UNKNOWN=0; }')
 def test_empty_and_comment_editor(self):
  self.assertEqual(label(source=' \r\n')['spans'],[]);self.encode('// comment\r\n')
if __name__=='__main__':unittest.main()
