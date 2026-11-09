import hashlib,json,tempfile,unittest
from pathlib import Path
from packs.c.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class CTeacherTests(unittest.TestCase):
    def test_independent_golden_and_original_coordinates(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);result=label(source=gold['source']);self.assertEqual(result['spans'],gold['spans'])
                encode({'source':gold['source'],'documentKind':'c','result':result,'contentHash':hashlib.sha256(gold['source'].encode()).hexdigest()},Schema.load(ROOT/'schema.json'))
    def test_callback_is_parameter_and_function_is_callable(self):
        source='typedef int (*Visit)(int n); int run(Visit fn) { return fn(3); }'
        r=label(source=source);start=source.index('fn(3)');self.assertIn('function-pointers',r['features']);self.assertIn({'start':start,'end':start+2,'tokenType':'parameter'},r['spans'])
    def test_macro_continuations_are_original_source(self):
        source='#define LOG(fmt, ...) \\\n printf(fmt, __VA_ARGS__)\n'
        r=label(source=source);text=[(source[s['start']:s['end']],s['tokenType']) for s in r['spans']]
        self.assertIn(('\\','punctuation'),text);self.assertIn(('printf','function'),text);self.assertIn(('__VA_ARGS__','parameter'),text)
    def test_bom_offsets_are_preserved(self):
        source='\ufeffint value;\r\n';r=label(source=source);self.assertEqual(r['spans'][0],{'start':0,'end':1,'tokenType':'punctuation'})
    def test_source_and_includes_are_not_executed_or_followed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'never-created';source='#include "missing.h"\nint main(void) { return system("touch '+str(path)+'"); }'
            self.assertTrue(label(source=source)['spans']);self.assertFalse(path.exists())
    def test_invalid_and_scope_are_quarantined(self):
        for s in ['int main( {','int x = "unfinished;']:
            with self.assertRaises(ValueError):label(source=s)
        with self.assertRaises(ValueError):label(source='int x;',document_kind='cpp')
        self.assertEqual(label(source='')['spans'],[])
if __name__=='__main__':unittest.main()
