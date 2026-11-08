"""Original versioned Vue grammar samples, independent of Golden and Playground."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

PROFILES = ("vue2", "vue3", "vue3.2")
def digest(raw): return hashlib.sha256(raw).hexdigest()

def examples(index, profile):
    n=index+20
    title=f"Entry {n} — 星 🌌"
    wrapper={"vue2":("<section v-cloak>","</section>"),"vue3":('<main role="region">',"</main>"),"vue3.2":('<article :aria-label="title" data-mode="setup">',"</article>")}[profile]
    binding=':open.sync="open" @click.native="save"' if profile=="vue2" else 'v-model:open="open" @update:open="save"'
    expression="amount | money('USD')" if profile=="vue2" else "formatAmount(amount)"
    script=(f'''<script>\nexport default {{
  name: 'Entry{n}',
  data() {{ return {{ title: '{title}', amount: {n}, open: true, items: [1, 2, 3] }}; }},
  methods: {{ save(value) {{ this.amount = value; }} }},
  filters: {{ money(value, unit) {{ return String(value) + unit; }} }}
}};\n</script>''' if profile=="vue2" else
    f'''<script>\nimport {{ ref }} from 'vue';
export default {{ setup() {{
  const title = ref('{title}'); const amount = ref({n}); const open = ref(true);
  const items = [1, 2, 3];
  const save = (value) => {{ amount.value = value; }};
  return {{ title, amount, open, items, save }};
}} }};\n</script>''' if profile=="vue3" else
    f'''<script setup lang="ts">\nimport {{ ref }} from 'vue';
interface Props {{ title?: string }}
const props = withDefaults(defineProps<Props>(), {{ title: '{title}' }});
const emit = defineEmits<{{ (event: 'save', value: number): void }}>();
const title = props.title; const amount = ref({n}); const open = ref(true);
const items = [1, 2, 3]; const save = () => emit('save', amount.value);
defineExpose({{ amount }});\n</script>''')
    lang=("css","scss","less")[index%3]
    style=(f'.entry-{n} {{ color: #3157ab; padding: {n}px; }}' if lang=="css" else
           f'$gap: {n}px; .entry-{n} {{ padding: $gap; color: #3157ab; }}' if lang=="scss" else
           f'@gap: {n}px; .entry-{n} {{ padding: @gap; color: #3157ab; }}')
    style=f'<style scoped lang="{lang}">\n{style}\n</style>'
    def template(body):return '<template>\n'+wrapper[0]+body+wrapper[1]+'\n</template>'
    legacy_slot=f'<span slot="heading">{title}</span><template slot="row" slot-scope="{{ row }}">{{{{ row.name }}}}</template>'
    slot=legacy_slot if profile=="vue2" else f'<template #heading>{title}</template><template #row="{{ row }}">{{{{ row.name }}}}</template>'
    bodies={
      'controls':f'<EntryCard {binding}><button v-if="open" @click.prevent="save">Save {n}</button><span v-else>Closed</span></EntryCard>',
      'lists':f'<ol><li v-for="(item, position) in items" :key="position" :class="{{ active: open }}">{{{{ position }}}}: {{{{ item }}}}</li></ol>',
      'slots':f'<EntryLayout>{slot}</EntryLayout>',
      'interpolations':f'<p>{{{{ {expression} }}}} / {{{{ title }}}}</p><output>{{{{ amount + {n} }}}}</output>',
      'dynamic-arguments':f'<EntryCard :[field]="amount" @[event].stop="save" v-focus:input.lazy="open"><span>{{{{ title }}}}</span></EntryCard>',
      'entity-and-strings':f'<p title="A &quot;note&quot;" class="grid md:gap-4 hover:bg-[#123456]">{title} &amp; notes &#x1f680; {{{{ title }}}}</p>',
      'comments':f'<!-- Entry header {n} -->\n<h2>{title}</h2><!-- status -->\n<small>{{{{ open ? "Open" : "Closed" }}}}</small>',
      'raw-text':f'<textarea name="example"><em>Literal {n}</em> &amp; text</textarea><pre v-pre>{{{{ literal }}}}</pre><span>{{{{ title }}}}</span>',
      'forms':f'<form @submit.prevent="save"><label>Count <input type="number" v-model.number="amount" required></label><button :disabled="!open">Save {n}</button></form>',
      'structural-components':f'<component :is="current" v-bind="options"><span>{{{{ title }}}}</span></component><transition name="fade"><aside v-show="open">{title}</aside></transition>',
      'short-fragments':f'<b>{{{{ title }}}}</b><i>{title}</i>',
      'foreign-content':f'<svg viewBox="0 0 20 20"><path :d="path"/><text>{{{{ title }}}}</text></svg><math><mi>x</mi></math>',
    }
    results={}
    for family,body in bodies.items():
        # Vary order and spacing, not a constant positional prefix.
        pieces=[template(body),script,style]
        if index%3==1:pieces=[script,template(body),style]
        elif index%3==2:pieces=[style,script,template(body)]
        results[family]='\n'*(index%3)+'\n\n'.join(pieces)
    jsx_kind='tsx' if index%2 else 'jsx'
    jsx=f'''<script lang="{jsx_kind}">\nexport const Badge = () => <strong class="badge">Entry {n}</strong>;\nexport default {{ components: {{ Badge }} }};\n</script>'''
    results['render-functions']=template('<Badge/>')+'\n'+jsx+'\n'+style
    results['custom-blocks']=template(f'<p>{title}</p>')+'\n'+script+f'\n<i18n lang="json">{{"en":{{"title":"Entry {n}"}}}}</i18n>\n'+style
    long_js='\n'.join(f'const item{n}_{i} = {{ label: "row-{i}", count: {i} }};' for i in range(14+index%7))
    results['long-bodies']=template(f'<h3>{title}</h3><p>{{{{ title }}}}</p>')+f'\n<script lang="ts">\n{long_js}\nexport const title = "{title}";\n</script>\n'+style
    return {k:v.replace('\n','\r\n') if index%4==0 else v for k,v in results.items()}

def generate(target:Path,variants=16):
    if not 4<=variants<=64:raise ValueError('Use a bounded 4..64 variants per family')
    identity={'kind':'original-vue-version-curriculum','version':2,'profiles':list(PROFILES),'variantsPerFamily':variants,'generatorHash':digest(Path(__file__).read_bytes())}
    if target.exists():
        lock=json.loads((target/'source.lock.json').read_text())
        if lock['identity']!=identity:raise ValueError('Preserve previous curriculum; choose another output directory')
        for name,sha in lock['files'].items():
            p=target/name
            if not p.resolve().is_relative_to(target.resolve()) or digest(p.read_bytes())!=sha:raise ValueError('Immutable curriculum changed')
        print('Reused Vue curriculum:',target);return
    target.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.curriculum-',dir=target.parent))
    try:
        files={}
        for profile in PROFILES:
            for index in range(variants):
                for family,source in examples(index,profile).items():
                    name=f'{profile}/{family}/example-{index:03d}.vue';p=staging/name;p.parent.mkdir(parents=True,exist_ok=True);raw=source.encode();p.write_bytes(raw);files[name]=digest(raw)
        lock={'identity':identity,'spec':{'name':'nsh-vue-curriculum','version':'2'},'integrity':'sha256:'+digest(json.dumps(identity,sort_keys=True).encode()),'files':dict(sorted(files.items()))}
        (staging/'source.lock.json').write_text(json.dumps(lock,indent=2)+'\n');staging.rename(target)
        print('Generated Vue curriculum:',len(files),'documents',target)
    finally:
        if staging.exists():shutil.rmtree(staging)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=Path(os.environ.get('NSH_DATASET_ROOT','~/Datasets/neural-semantic-highlighting')).expanduser()/'vue/sources/curriculum-v2');p.add_argument('--variants',type=int,default=16);a=p.parse_args();generate(a.output.expanduser().resolve(),a.variants)
if __name__=='__main__':main()
