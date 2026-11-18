import hashlib,json,unittest
from pathlib import Path
from packs.diff.labeling.label import label
from training.shared.golden import unmark
from training.shared.encoding import Schema,encode
ROOT=Path(__file__).parents[1]
class DiffTeacherTests(unittest.TestCase):
 def encode(self,s):
  r=label(source=s)
  if s:encode(dict(source=s,documentKind='diff',result=r,contentHash=hashlib.sha256(s.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
  return r
 def test_independent_marked_original_line_ranges(self):
  for c in json.loads((ROOT/'fixtures/golden.json').read_text()):
   with self.subTest(case=c['id']):
    g=unmark(c['markedSource']);self.assertEqual(self.encode(g['source'])['spans'],g['spans'])
 def test_wrong_counts_and_bad_headers_fail_closed(self):
  for s in ['--- a/x\n+++ b/x\n@@ -1,2 +1 @@\n-a\n+b\n','--- a/x\n+++ b/x\n@@ broken @@\n-a\n+b\n','diff --cc x\n@@@ -1 -1 +1 @@@\n++x\n','\x1b[31m-old\n']:
   with self.subTest(source=s):
    with self.assertRaises(ValueError):self.encode(s)
 def test_original_source_is_not_applied_or_executed(self):
  self.encode('--- a/does-not-exist\n+++ b/does-not-exist\n@@ -1 +1 @@\n-$(never run)\n+<script>source only</script>\n')
 def test_complete_hunk_body_has_priority_over_header_spelling(self):
  r=self.encode('--- a/x\n+++ b/x\n@@ -1 +1 @@\n---- x\n++++ y\n');self.assertEqual([s['tokenType']for s in r['spans']][-2:],['deletion','addition'])
 def test_empty_and_profile_guard(self):
  self.assertEqual(self.encode(' \r\n')['spans'],[dict(start=0,end=1,tokenType='text')]);self.assertEqual(label(source='')['spans'],[])
  with self.assertRaises(ValueError):label(source='',profile='patch')
 def test_unicode_line_separator_is_payload_not_physical_newline(self):
  r=self.encode('-a\u2028b\n+c\u2029d\n');self.assertEqual(len(r['spans']),2)
if __name__=='__main__':unittest.main()
