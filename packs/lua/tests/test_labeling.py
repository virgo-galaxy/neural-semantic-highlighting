import hashlib,json,unittest
from pathlib import Path
from packs.lua.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class LuaTeacherTests(unittest.TestCase):
    def test_independent_marked_golden_original_utf16(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);result=label(source=gold['source']);self.assertEqual(result['spans'],gold['spans'])
                if gold['source']:encode(dict(source=gold['source'],documentKind='lua',result=result,contentHash=hashlib.sha256(gold['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_local_initializer_sees_outer_parameter_before_new_binding(self):
        source='local function f(x) do local x=x; print(x) end; return x end';spans=label(source=source)['spans'];at=source.index('=x')+1
        self.assertIn(dict(start=at,end=at+1,tokenType='parameter'),spans);at=source.index('print(x)')+6;self.assertIn(dict(start=at,end=at+1,tokenType='variable'),spans)
    def test_closure_initializer_does_not_see_its_new_local(self):
        source='local function outer(f) local f=function() return f end; return f end';s=label(source=source)['spans'];at=source.index('return f')+7;self.assertIn(dict(start=at,end=at+1,tokenType='parameter'),s);at=source.rindex('return f')+7;self.assertIn(dict(start=at,end=at+1,tokenType='function'),s)
    def test_local_function_is_visible_recursively(self):
        source='local function f() return f end';s=label(source=source)['spans'];at=source.index('return f')+7;self.assertIn(dict(start=at,end=at+1,tokenType='function'),s)
    def test_loop_bounds_see_outer_and_body_sees_loop_binding(self):
        source='local function f(i) for i=i,3 do print(i) end; return i end';s=label(source=source)['spans'];at=source.index('=i')+1;self.assertIn(dict(start=at,end=at+1,tokenType='parameter'),s);at=source.index('print(i)')+6;self.assertIn(dict(start=at,end=at+1,tokenType='variable'),s);at=source.rindex('return i')+7;self.assertIn(dict(start=at,end=at+1,tokenType='parameter'),s)
    def test_repeat_local_is_visible_in_until_condition(self):
        source='local function f(done) repeat local done<const> = true until done; return done end';s=label(source=source)['spans'];at=source.index('until done')+6;self.assertIn(dict(start=at,end=at+4,tokenType='constant'),s);at=source.rindex('return done')+7;self.assertIn(dict(start=at,end=at+4,tokenType='parameter'),s)
    def test_colon_method_binds_implicit_self_only_inside(self):
        source='function M:add(x) return self.count+x end; print(self)';s=label(source=source)['spans'];at=source.index('self.count');self.assertIn(dict(start=at,end=at+4,tokenType='parameter'),s);at=source.rindex('self');self.assertIn(dict(start=at,end=at+4,tokenType='variable'),s)
    def test_computed_table_key_is_expression_not_property_declaration(self):
        source='local key="title"; local t={[key]=1, title=2}';s=label(source=source)['spans'];at=source.index('[key]')+1;self.assertIn(dict(start=at,end=at+3,tokenType='variable'),s)
    def test_callback_keeps_parameter_role(self):
        source='local function f(callback) return callback(1) end';s=label(source=source)['spans'];at=source.rindex('callback');self.assertIn(dict(start=at,end=at+8,tokenType='parameter'),s)
    def test_long_strings_never_scan_fake_code_or_interpolation(self):
        source='return [==[-- comment #{x} ${y} [[inner]] ]=] text]==]';self.assertEqual(label(source=source)['spans'],[dict(start=0,end=6,tokenType='keyword'),dict(start=7,end=len(source),tokenType='string')])
    def test_lua55_global_attributes_and_named_varargs_parse_without_sdk(self):
        for source in ['global none\nglobal<const> LIMIT=3\n','local function f(...args) return args, ... end']:
            result=label(source=source);encode(dict(source=source,documentKind='lua',result=result,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_unicode_crlf_original_ranges_encode(self):
        source='-- 🌌\r\nlocal text=[=[星\r\n-- raw]=]\r\n';result=label(source=source);encode(dict(source=source,documentKind='lua',result=result,contentHash=hashlib.sha256(source.encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_invalid_source_fails_closed(self):
        for source in ['local function f(', 'local x=[=[missing', '\0']:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):label(source=source)
if __name__=='__main__':unittest.main()
