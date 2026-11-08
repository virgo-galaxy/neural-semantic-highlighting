import hashlib
import json
from pathlib import Path
import unittest
from packs.perl.labeling.label import label
from training.shared.golden import unmark
from training.shared.encoding import Schema,encode

class PerlTeacherTests(unittest.TestCase):
    def test_independent_golden(self):
        root=Path(__file__).parents[1]
        for case in json.loads((root/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource']);result=label(source=gold['source'])
                self.assertEqual(result['spans'],gold['spans'])
                encode({'source':gold['source'],'documentKind':'perl','result':result,'contentHash':hashlib.sha256(gold['source'].encode()).hexdigest()},Schema.load(root/'schema.json'))

    def test_source_never_executes(self):
        self.assertTrue(label(source='BEGIN { die "this must not run"; }\n')['spans'])

    def test_missing_heredoc_terminator_rejected(self):
        with self.assertRaises(ValueError):label(source='my $text = <<EOF;\nno terminator\n')

    def test_unicode_sigil_and_crlf(self):
        source='use utf8;\r\n\tmy $名字 = "星 🌌";\r\n'
        raw=source.encode('utf-16-le');spans=label(source=source)['spans']
        variable=next(s for s in spans if raw[s['start']*2:s['end']*2].decode('utf-16-le')=='$名字')
        self.assertEqual(variable['tokenType'],'variable');self.assertEqual(variable['modifiers'],['declaration'])

    def test_physical_locations_ignore_line_directive(self):
        source='#line 900 "elsewhere.pl"\nmy $value = 1;\n'
        spans=label(source=source)['spans'];self.assertTrue(all(s['end']<=len(source) for s in spans))

    def test_opaque_signature_and_regular_expression(self):
        source='sub greet ($name, $limit=2) { return $name; }\nmy $rule = qr{[a-z]+}i;\n'
        roles={s['tokenType'] for s in label(source=source)['spans']}
        self.assertIn('parameter',roles);self.assertIn('regexp',roles)

if __name__=='__main__':unittest.main()
