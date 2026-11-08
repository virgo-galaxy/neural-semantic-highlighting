import json
from pathlib import Path
import unittest
from packs.bash.labeling.label import label
from training.shared.golden import unmark

class ShellTeacherTests(unittest.TestCase):
    def test_independent_golden(self):
        for case in json.loads((Path(__file__).parents[1]/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                gold=unmark(case['markedSource'])
                self.assertEqual(label(source=gold['source'],profile=case['profile'])['spans'],gold['spans'])

    def test_no_source_execution(self):
        self.assertTrue(label(source='unavailable-command --never-run\n')['spans'])

    def test_multiple_heredocs_and_exact_terminator_lines(self):
        marked="⟦function|cat⟧ ⟦string|<<A⟧ ⟦string|<<'B'⟧\r\n⟦string|A appears inside a line\r\nA⟧\r\n⟦string|星空 🌌 $name\r\nB⟧\r\n⟦function+default-library|echo⟧ ⟦string|ready⟧\r\n"
        gold=unmark(marked)
        result=label(source=gold['source'])
        self.assertEqual(result['spans'],gold['spans'])
        self.assertIn('heredocs',result['features'])

    def test_heredoc_exclusions_and_incomplete_source(self):
        for source in ['echo "<<EOF"\n', '# cat <<EOF\n', 'echo $((1 << 2))\n', 'cat <<< "$value"\n']:
            self.assertNotIn('heredocs',label(source=source)['features'])
        with self.assertRaises(ValueError): label(source='cat <<EOF\nmissing terminator\n')

    def test_builtin_shadow_and_environment_prefix(self):
        source='echo() { printf ready; }\nTOKEN="$token" run --fast\necho done\n'
        result=label(source=source);raw=source.encode('utf-16-le')
        names=[s for s in result['spans'] if raw[s['start']*2:s['end']*2].decode('utf-16-le')=='echo']
        self.assertEqual(names[0].get('modifiers'),['declaration'])
        self.assertNotIn('modifiers',names[-1])
        run=next(s for s in result['spans'] if raw[s['start']*2:s['end']*2].decode('utf-16-le')=='run')
        self.assertEqual(run['tokenType'],'function')

    def test_unsupported_profiles_rejected(self):
        with self.assertRaises(ValueError):label(source='echo yes',profile='powershell')

    def test_parameter_expansion_and_attached_redirection(self):
        marked='⟦variable+declaration|cache⟧⟦operator|=⟧⟦operator|${⟧⟦variable|CACHE⟧⟦operator|:-⟧⟦string|/tmp/cache⟧⟦operator|}⟧\n⟦function+default-library|echo⟧ ⟦string|ready⟧⟦operator|>⟧⟦string|out⟧\n⟦function|sort⟧⟦operator|<⟧⟦string|input⟧\n'
        gold=unmark(marked)
        self.assertEqual(label(source=gold['source'])['spans'],gold['spans'])

    def test_declaration_rhs_is_not_a_declaration(self):
        for profile,source in [('bash','export NAME=ready\n'),('csh','setenv NAME ready\n')]:
            with self.subTest(profile=profile):
                result=label(source=source,profile=profile);raw=source.encode('utf-16-le')
                span=next(s for s in result['spans'] if raw[s['start']*2:s['end']*2].decode('utf-16-le')=='ready')
                self.assertEqual(span['tokenType'],'string');self.assertNotIn('modifiers',span)

    def test_csh_arithmetic(self):
        marked='⟦operator|@⟧ ⟦variable+declaration|count⟧ ⟦operator|=⟧ ⟦number|2⟧\n⟦operator|@⟧ ⟦variable+declaration|next⟧ ⟦operator|=⟧ ⟦punctuation|(⟧ ⟦variable|$count⟧ ⟦operator|+⟧ ⟦number|1⟧ ⟦punctuation|)⟧\n'
        gold=unmark(marked)
        self.assertEqual(label(source=gold['source'],profile='csh')['spans'],gold['spans'])
        self.assertNotIn('arrays',label(source=gold['source'],profile='csh')['features'])

    def test_shared_syntax_has_shared_quoted_variable_labels(self):
        source='echo "Hello $name"\n'
        expected=label(source=source,profile='bash')['spans']
        for profile in ['posix','zsh','csh']:
            self.assertEqual(label(source=source,profile=profile)['spans'],expected)

    def test_leading_loop_and_array_coverage_tags(self):
        self.assertIn('leading-loops',label(source='foreach name ( alpha beta )\n echo $name\nend\n',profile='csh')['features'])
        self.assertIn('arrays',label(source='set names = ( alpha beta )\n',profile='csh')['features'])

    def test_csh_switch_delimiters_and_control_builtins(self):
        marked='⟦keyword|switch⟧ ⟦punctuation|(⟧ ⟦string|"⟧⟦variable|$mode⟧⟦string|"⟧ ⟦punctuation|)⟧\n⟦keyword|case⟧ ⟦string|ready⟧⟦punctuation|:⟧\n ⟦keyword|breaksw⟧\n⟦keyword|default⟧⟦punctuation|:⟧\n ⟦keyword|breaksw⟧\n⟦keyword|endsw⟧\n'
        gold=unmark(marked)
        self.assertEqual(label(source=gold['source'],profile='csh')['spans'],gold['spans'])

if __name__=='__main__':unittest.main()
