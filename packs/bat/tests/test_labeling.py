import hashlib,json
from pathlib import Path
import unittest
from packs.bat.labeling.label import label
from training.shared.golden import unmark
from training.shared.encoding import Schema,encode
class BatchTeacherTests(unittest.TestCase):
 def test_independent_golden_and_original_coordinates(self):
  root=Path(__file__).parents[1]
  for case in json.loads((root/'fixtures/golden.json').read_text()):
   with self.subTest(case=case['id']):
    gold=unmark(case['markedSource']);result=label(source=gold['source']);self.assertEqual(result['spans'],gold['spans'])
    encode({'source':gold['source'],'documentKind':'bat','result':result,'contentHash':hashlib.sha256(gold['source'].encode()).hexdigest()},Schema.load(root/'schema.json'))
 def test_source_is_never_executed(self):
  self.assertTrue(label(source='del /s dangerous_placeholder\n')['spans'])
 def test_loop_modifiers_are_one_variable(self):
  source='for %%A in (*.txt) do echo %%~dpnxA\n';raw=source.encode('utf-16-le');v=[raw[s['start']*2:s['end']*2].decode('utf-16-le') for s in label(source=source)['spans'] if s['tokenType']=='variable'];self.assertEqual(v,['%%A','%%~dpnxA'])
 def test_extensions_share_document_kind(self):
  m=json.loads((Path(__file__).parents[1]/'manifest.json').read_text());self.assertEqual(m['documentKinds'],[{'id':'bat','extensions':['.bat','.cmd']}])
 def test_nested_for_f_command_quotes_do_not_scan_later_lines(self):
  source = "for /f \"delims=\" %%i in ('node -p \"require('fs').realpathSync.native(require('os').tmpdir())\"') do set TEMPVAR=%%i\n" + 'set RESULT=%TEMPVAR%\n' * 20 + 'echo complete\n'
  result=label(source=source);raw=source.encode('utf-16-le')
  echo=[s for s in result['spans'] if raw[s['start']*2:s['end']*2].decode('utf-16-le')=='echo'];self.assertEqual(echo[-1]['tokenType'],'keyword')
if __name__=='__main__':unittest.main()
