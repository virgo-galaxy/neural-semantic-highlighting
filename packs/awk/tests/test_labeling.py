import hashlib,json
from pathlib import Path
import unittest
from packs.awk.labeling.label import label
from training.shared.golden import unmark
from training.shared.encoding import Schema,encode

class AwkTeacherTests(unittest.TestCase):
    def test_independent_golden(self):
        root=Path(__file__).parents[1]
        for case in json.loads((root/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);result=label(source=gold['source'])
                self.assertEqual(result['spans'],gold['spans'])
                encode({'source':gold['source'],'documentKind':'awk','result':result,'contentHash':hashlib.sha256(gold['source'].encode()).hexdigest()},Schema.load(root/'schema.json'))

    def test_source_not_executed(self):
        self.assertTrue(label(source='BEGIN { exit 99 }\n')['spans'])

    def test_division_and_regex_features(self):
        result=label(source='{ print $2 / 3; if ($1 ~ /abc/) next }\n')
        self.assertIn('fields',result['features']);self.assertIn('regexps',result['features'])

    def test_function_local_names(self):
        source='function render(value, temp) { temp = value; return temp }\n'
        result=label(source=source);raw=source.encode('utf-16-le')
        names=[raw[x['start']*2:x['end']*2].decode('utf-16-le') for x in result['spans'] if x.get('modifiers')==['declaration']]
        self.assertEqual(names,['render','value','temp'])

    def test_gnu_switch_regular_expression(self):
        source='{ switch ($1) { case /warn/: print $0; break; default: next } }\n'
        self.assertIn('regexp',{s['tokenType'] for s in label(source=source)['spans']})

if __name__=='__main__':unittest.main()
