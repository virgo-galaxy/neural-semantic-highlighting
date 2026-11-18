import hashlib,json,unittest
from pathlib import Path
from packs.graphql.labeling.label import label
from training.shared.golden import unmark
from training.shared.encoding import Schema,encode
ROOT=Path(__file__).parents[1]
class GraphqlTeacherTests(unittest.TestCase):
 def encode(self,source):
  result=label(source=source)
  if source:encode(dict(source=source,documentKind='graphql',result=result,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
  return result
 def test_independently_marked_original_ranges(self):
  for c in json.loads((ROOT/'fixtures/golden.json').read_text()):
   with self.subTest(case=c['id']):
    g=unmark(c['markedSource']);self.assertEqual(self.encode(g['source'])['spans'],g['spans'])
 def test_invalid_source_and_wrong_profile_fail(self):
  for s in ['query {','type X { bad }','{f(a: 01)}','{f(a:"bad\\q")}','{f}\0']:
   with self.subTest(source=s):
    with self.assertRaises(ValueError):label(source=s)
  with self.assertRaises(ValueError):label(source='{id}',profile='proto')
 def test_strings_and_descriptions_are_original_opaque_source(self):
  s='"""\r\n# literal 🌌 {a: true}\r\n"""\ntype X { f: String }';r=self.encode(s);self.assertEqual(r['spans'][0]['tokenType'],'string');self.assertEqual(r['spans'][0]['end'],len(s[:s.index('\ntype')].encode('utf-16-le'))//2)
 def test_keyword_spelling_is_ast_local(self):
  r=self.encode('{ query type null }');self.assertEqual([s['tokenType']for s in r['spans']],['punctuation','property','property','property','punctuation'])
 def test_empty_comment_editor_and_no_schema_or_execution_needed(self):
  self.assertEqual(label(source=' \r\n')['spans'],[]);self.encode('# comment\r\n');self.encode('query Unsafe { missing(argument: "$(never run)") }')
if __name__=='__main__':unittest.main()
