import hashlib,json
from pathlib import Path
import unittest
from packs.powershell.labeling.label import label
from training.shared.golden import unmark
from training.shared.encoding import Schema,encode
class PowerShellTeacherTests(unittest.TestCase):
 def test_independent_golden_and_original_coordinates(self):
  root=Path(__file__).parents[1]
  for case in json.loads((root/'fixtures/golden.json').read_text()):
   with self.subTest(case=case['id']):
    gold=unmark(case['markedSource']);result=label(source=gold['source'])
    self.assertEqual(result['spans'],gold['spans'])
    encode({'source':gold['source'],'documentKind':'powershell','result':result,'contentHash':hashlib.sha256(gold['source'].encode()).hexdigest()},Schema.load(root/'schema.json'))
 def test_input_is_never_executed(self):
  self.assertTrue(label(source='Remove-Item -Recurse dangerous_placeholder\n')['spans'])
 def test_here_string_is_opaque_and_ends_before_next_command(self):
  source='$x = @"\n$name <# text #>\n"@\nGet-Date\n';raw=source.encode('utf-16-le');spans=label(source=source)['spans']
  self.assertEqual([raw[s['start']*2:s['end']*2].decode('utf-16-le') for s in spans if s['tokenType']=='string'],['@"\n$name <# text #>\n"@'])
 def test_defined_hyphen_function_is_not_builtin(self):
  source='function Read-Note { return 1 }\nRead-Note\n';raw=source.encode('utf-16-le');spans=label(source=source)['spans']
  names=[s for s in spans if raw[s['start']*2:s['end']*2].decode('utf-16-le')=='Read-Note'];self.assertEqual(names[-1].get('modifiers',[]),[])
 def test_range_numbers_are_covered(self):
  source='1..8 | ForEach-Object { $_ * 2 }\n';raw=source.encode('utf-16-le')
  numbers=[raw[s['start']*2:s['end']*2].decode('utf-16-le') for s in label(source=source)['spans'] if s['tokenType']=='number']
  self.assertEqual(numbers,['1','8','2'])
if __name__=='__main__':unittest.main()
