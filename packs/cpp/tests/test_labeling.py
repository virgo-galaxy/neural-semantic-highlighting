import hashlib,json,tempfile,unittest
from pathlib import Path
from packs.cpp.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class CppTeacherTests(unittest.TestCase):
    def test_independent_golden_and_original_coordinates(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);r=label(source=gold['source']);self.assertEqual(r['spans'],gold['spans']);encode(dict(source=gold['source'],documentKind='cpp',result=r,contentHash=hashlib.sha256(gold['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_template_scope_and_member_calls(self):
        source='template<class T> T f(T value){return value;} void g(){ T other; item.read(); }'
        r=label(source=source);tokens=[(source[s['start']:s['end']],s['tokenType']) for s in r['spans']]
        self.assertIn(('item','variable'),tokens);self.assertIn(('read','function'),tokens);self.assertEqual([role for text,role in tokens if text=='T'][-1],'type')
    def test_lambda_parameters_and_structured_bindings(self):
        source='void run(){ auto [left,right]=pair; auto fn=[offset=2](int n){return n+offset;}; fn(left); }'
        r=label(source=source);items=[(source[s['start']:s['end']],s) for s in r['spans']];self.assertTrue(any(t=='right' and s.get('modifiers')==['declaration'] for t,s in items));self.assertEqual([s['tokenType'] for t,s in items if t=='n'],['parameter','parameter'])
    def test_constrained_template_parameter(self):
        source='template<class U> concept Addable=requires(U n){n+n;}; template<Addable T> T sum(T a,T b){return a+b;}'
        r=label(source=source);roles=[s['tokenType'] for s in r['spans'] if source[s['start']:s['end']]=='T'];self.assertEqual(roles,['type-parameter']*4)
    def test_raw_strings_bom_and_crlf(self):
        source='\ufeff// 原始 🌙\r\nauto text=R"x(a "🌌"\r\nb)x";\r\n';r=label(source=source);self.assertEqual(r['spans'][0]['start'],0);strings=[s for s in r['spans'] if s['tokenType']=='string'];self.assertEqual(len(strings),1);raw=source.encode('utf-16-le');self.assertEqual(raw[strings[0]['start']*2:strings[0]['end']*2].decode('utf-16-le'),'R"x(a "🌌"\r\nb)x"')
    def test_macro_continuations(self):
        source='#define APPLY(x) \\\n ((x)+1)\n';r=label(source=source);self.assertIn('macros',r['features']);self.assertTrue(any(source[s['start']:s['end']]=='\\' for s in r['spans']))
    def test_source_and_includes_are_not_executed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'never-created';self.assertTrue(label(source='#include "missing.hpp"\nint main(){return system("touch '+str(path)+'");}')['spans']);self.assertFalse(path.exists())
    def test_invalid_scope_and_empty_source(self):
        for source in ['class Broken {','auto s = "unfinished;']:
            with self.assertRaises(ValueError):label(source=source)
        with self.assertRaises(ValueError):label(source='int value;',document_kind='c')
        self.assertEqual(label(source='')['spans'],[])
if __name__=='__main__':unittest.main()
