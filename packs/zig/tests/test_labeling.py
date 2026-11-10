import hashlib,json,tempfile,unittest
from pathlib import Path
from packs.zig.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class ZigTeacherTests(unittest.TestCase):
    def test_independent_golden_original_utf16(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                g=unmark(case['markedSource']);r=label(source=g['source']);self.assertEqual(r['spans'],g['spans']);encode(dict(source=g['source'],documentKind='zig',result=r,contentHash=hashlib.sha256(g['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_current_builtin_arity_rejects_old_forms(self):
        for s in ['fn f(x:u32) u8 {return @intCast(u8,x);}','fn f(x:*u8) usize {return @ptrToInt(x);}','async fn f() void {}']:
            with self.assertRaises(ValueError):label(source=s)
    def test_comptime_imports_and_embed_files_are_not_evaluated(self):
        s='const missing=@import("does-not-exist.zig"); const data=@embedFile("missing-data"); comptime { @compileError("must never evaluate input"); }';self.assertTrue(label(source=s)['spans'])
    def test_anonymous_function_type_parameters_do_not_leak(self):
        s='const Callback=*const fn(value:u32) void; fn f() void { const value:u32=1; _=value; }';r=label(source=s);at=s.rindex('value');self.assertIn(dict(start=at,end=at+5,tokenType='variable'),r['spans'])
    def test_current_capture_nodes_and_type_parameters(self):
        s='fn Box(comptime T:type) type { return struct{value:T}; } fn f(items:[]const u8) void { for(items,0..) |item,index| { _=item; _=index; } }';r=label(source=s);self.assertIn('captures',r['features']);self.assertIn('comptime',r['features']);self.assertTrue(any(x['tokenType']=='type-parameter' and not x.get('modifiers') for x in r['spans']));self.assertEqual(sum(x['tokenType']=='variable' and x.get('modifiers')==['declaration'] for x in r['spans']),2)
    def test_comment_gaps_do_not_reparse_strings_or_multiline_text(self):
        s='// ordinary 🌌\nconst a="// string";\nconst b=\n\\\\// literal\n;\n';r=label(source=s);self.assertEqual(sum(x['tokenType']=='comment' for x in r['spans']),1);self.assertEqual(sum(x['tokenType']=='string' for x in r['spans']),2)
    def test_quoted_unicode_bom_crlf_original_bytes(self):
        s='\ufeffconst @"星 🌌":u8=1;\r\n';r=label(source=s);self.assertEqual(r['spans'][0],dict(start=0,end=1,tokenType='punctuation'));encode(dict(source=s,documentKind='zig',result=r,contentHash=hashlib.sha256(s.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_current_contextual_call_is_a_function(self):
        s='fn f() void { const value:Thing=.init(); _=value; }';r=label(source=s);at=s.index('init');self.assertIn(dict(start=at,end=at+4,tokenType='function'),r['spans'])
    def test_invalid_input_is_quarantined(self):
        for s in ['fn broken( {','const text="unfinished;','/* block comments are not Zig */']:
            with self.assertRaises(ValueError):label(source=s)
        with self.assertRaises(ValueError):label(source='const x=1;',document_kind='zon')
        self.assertEqual(label(source='')['spans'],[])
if __name__=='__main__':unittest.main()
