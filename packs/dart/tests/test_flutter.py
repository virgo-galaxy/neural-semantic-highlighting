import hashlib,json,unittest
from pathlib import Path
from packs.dart.labeling.label import label
from training.shared.golden import unmark
from training.shared.encoding import Schema,encode

ROOT=Path(__file__).parents[1]
class FlutterGoldenTests(unittest.TestCase):
    def test_independent_flutter_roles_and_original_offsets(self):
        for case in json.loads((ROOT/'fixtures/flutter-golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);actual=label(source=gold['source'])
                self.assertEqual(actual['spans'],gold['spans'])
                encode(dict(source=gold['source'],documentKind='dart',result=actual,contentHash=hashlib.sha256(gold['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
if __name__=='__main__':unittest.main()
