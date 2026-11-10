import hashlib,json,tempfile,unittest
from pathlib import Path
from packs.svelte.labeling.label import label
from training.shared.encoding import Schema,encode
from training.shared.golden import unmark
ROOT=Path(__file__).parents[1]
class SvelteTeacherTests(unittest.TestCase):
    def test_independent_golden_original_coordinates(self):
        for case in json.loads((ROOT/'fixtures/golden.json').read_text()):
            with self.subTest(case=case['id']):
                g=unmark(case['markedSource']);r=label(source=g['source']);self.assertEqual(r['spans'],g['spans']);encode(dict(source=g['source'],documentKind='svelte',result=r,contentHash=hashlib.sha256(g['source'].encode()).hexdigest()),Schema.load(ROOT/'schema.json'))
    def test_styles_are_original_not_masked(self):
        for lang,body in [('scss','$a: red; .x { color: $a; }'),('less','@a: 2px; .x { gap: @a; }')]:
            source=f'<style lang="{lang}">{body}</style>';r=label(source=source);s=next(x for x in r['spans'] if x['tokenType']=='embedded-'+lang);self.assertEqual(source[s['start']:s['end']],body)
    def test_dynamic_component_target_stays_attribute(self):
        s='<svelte:component this={target} {value} />';r=label(source=s);self.assertEqual([s[x['start']:x['end']] for x in r['spans'] if x['tokenType']=='string'],['{target}'])
    def test_incomplete_components_are_quarantined(self):
        for s in ['{#if ready}<p>Hi</p>','<script>let = ;</script>','<p>{unclosed</p>']:
            with self.assertRaises(ValueError):label(source=s)
        with self.assertRaises(ValueError):label(source='<p />',document_kind='html')
    def test_source_imports_and_handlers_are_not_executed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'never-created';s='<script>import "missing-module"; import fs from "node:fs"; fs.writeFileSync('+json.dumps(str(path))+', "bad");</script><p>Hi</p>';self.assertTrue(label(source=s)['spans']);self.assertFalse(path.exists())
    def test_legacy_and_runes_regions_share_child_languages(self):
        for s in ['export let value=1; $: doubled=value*2;','let value=$state(1); let doubled=$derived(value*2);']:
            r=label(source='<script>'+s+'</script>');self.assertEqual([x['tokenType'] for x in r['spans']].count('embedded-javascript'),1)
if __name__=='__main__':unittest.main()
