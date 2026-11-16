import hashlib,json,unittest
from pathlib import Path
from packs.markdown.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class MarkdownTeacherTests(unittest.TestCase):
 def check(self,source):
  r=label(source=source)
  if source:encode(dict(source=source,documentKind='markdown',result=r,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
  return r
 def test_independent_marked_original_ranges(self):
  for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
   with self.subTest(case=case['id']):
    g=unmark(case['markedSource']);self.assertEqual(self.check(g['source'])['spans'],g['spans'])
 def test_original_unicode_bom_and_crlf_roundtrip(self):
  src='\ufeff# 星空 🌌\r\n\r\n**原文 👩🏽‍💻**\r\n';r=self.check(src);self.assertEqual(r['spans'][0],dict(start=0,end=1,tokenType='punctuation'));self.assertEqual(r['spans'][-1]['end'],len(src.rstrip('\r\n').encode('utf-16-le'))//2)
 def test_fence_body_has_original_contiguous_region(self):
  src='```js title=test\r\nconst n = 1;\r\n```\r\n';r=self.check(src);span=next(s for s in r['spans']if s['tokenType']=='embedded-code');self.assertEqual(src[span['start']:span['end']],'const n = 1;\r\n')
 def test_unknown_and_missing_language_are_not_guessed(self):
  for src in ['```unknown\nconst n = 1;\n```','```\nconst n = 1;\n```']:
   self.assertEqual(sum(s['tokenType']=='embedded-code'for s in self.check(src)['spans']),1)
 def test_empty_and_unclosed_fences_keep_existing_source_only(self):
  self.assertFalse(any(s['tokenType']=='embedded-code'for s in self.check('```js\n```')['spans']));self.assertEqual(self.check('```js\nconst n=1;')['spans'][-1]['end'],len('```js\nconst n=1;'))
 def test_longer_fences_can_contain_short_backticks(self):
  src='````md\n```js\nconst x=1;\n```\n````';r=self.check(src);self.assertEqual(sum(s['tokenType']=='embedded-code'for s in r['spans']),1)
 def test_nested_and_indented_code_stays_opaque(self):
  for src in ['> ```js\n> const x = 1;\n> ```','- Item\n\n  ```js\n  const x = 1;\n  ```','    const x = 1;']:
   r=self.check(src);self.assertFalse(any(s['tokenType']=='embedded-code'for s in r['spans']));self.assertTrue(any(s['tokenType']=='code'for s in r['spans']))
 def test_nested_modifiers_keep_both(self):
  r=self.check('**bold *both***');self.assertTrue(any(s.get('modifiers')==['strong','emphasis']for s in r['spans']))
 def test_gfm_table_and_task_features(self):
  r=self.check('| A | B |\n| --- | --- |\n| x | y |\n\n- [x] done\n');self.assertTrue({'tables','tasks','lists'}<=set(r['features']))
 def test_entities_and_escapes_do_not_decode_source(self):
  src='&amp; &#x1F30C; \\* &unknown;';r=self.check(src);self.assertEqual(sum(s['tokenType']=='entity'for s in r['spans']),3)
 def test_frontmatter_and_html_are_opaque(self):
  for src in ['---\nname: preview\n---','<script>neverExecute()</script>']:
   r=self.check(src);self.assertFalse(any(s['tokenType']=='embedded-code'for s in r['spans']))
 def test_prose_copy_shape_normalizes_new_markdown_roles(self):
  schema=Schema.load(ROOT/'schema.json');shapes=[]
  for src in ['# First\n\n[One](https://one.test)\n\n`alpha()`','# Second\n\n[Two](https://two.test)\n\n`beta()`']:
   r=self.check(src);shapes.append(encode(dict(source=src,documentKind='markdown',result=r,contentHash=hashlib.sha256(src.encode()).hexdigest()),schema).shape_hash)
  self.assertEqual(*shapes)
 def test_empty_editor_input_and_kind_profile_guard(self):
  self.assertEqual(self.check(' \r\n')['spans'],[])
  with self.assertRaises(ValueError):label(source='# Hi',document_kind='mdx')
  with self.assertRaises(ValueError):label(source='# Hi',profile='mdx')
 def test_bad_source_and_unexpected_parser_nodes_fail_closed(self):
  with self.assertRaises(ValueError):self.check('A\0B')
if __name__=='__main__':unittest.main()
