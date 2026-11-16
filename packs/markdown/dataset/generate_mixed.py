"""Original varied prose/link/frontmatter compositions after actual source review."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
WORDS='amber birch cedar dawn estuary fern grove harbor iris jade kiln lake meadow nook orchard pebble river shore tulip vale'.split()
PARAGRAPHS=[
 'The @W@ interface keeps its original source when a document changes. It may contain\nseveral wrapped lines, `inline_value`, and a later reference to the same value.\nThe complete paragraph stays prose until an actual Markdown marker begins.',
 'A `parent value` is checked, a `child value` is ready, and the middle item remains\nunmodified. Parentheses (including their contents), quotes "like these", and\nordinary punctuation do not begin a source-code string.',
 'For @W@, use **strong wording** near a link and *emphasis across\nwrapped lines*. Leave ~~earlier wording~~ visible and preserve the rest of the\nparagraph without replacing whitespace or joining source lines.',
 'Read the [@W@ guide](https://example.test/docs/@W@ "The guide") before continuing.\nA destination may include [balanced parentheses](https://example.test/a_(b)) or\n[an explicit target](<https://example.test/a%20b>).',
 '原文 @W@ 包含多个换行，但仍然是同一个段落。这里有 **重要文字** 和 `代码片段`，\n也有普通标点、括号（保留原样）与 星空 🌌。下一行继续描述同一件事情，\n不应把每一个汉字都划成独立的标记。',
 'Visit <https://example.test/@W@> or https://example.test/@W@ for the same source.\nThe address <reader@example.test> stays an autolink. A literal &amp; reference\nand an escaped \\*marker\\* keep their original spellings.',
 'An image such as ![@W@ preview](./assets/@W@.svg "Preview") stays source text.\nUse the [API guide][@W@-api] or [@W@-home] for additional details.\nNeither a link nor an image should cause a network request.',
 'Several inline fragments appear together: `alpha(@N@)`, `beta(@N@ + 1)` and\n`` nested `ticks` ``. The prose between them stays ordinary text, even when it\ncontains a slash/path, equals=value, or quoted "notes".'
]
def main():
 from packs.markdown.labeling.label import label
 root=PackSpec.open('markdown').dataset_root/'sources/mixed-v1';files={}
 for layout in range(8):
  for sections in range(1,4):
   family=f'prose-{layout}-{sections}'
   for v in range(24):
    w=WORDS[(layout*3+sections+v)%len(WORDS)];n=str(random.Random(221+layout*317+sections*23+v).randrange(7,90));replace=lambda t:t.replace('@W@',w).replace('@N@',n)
    parts=[]
    if v%3!=1:parts+=['---','title: '+w+' documentation','description: "A long '+w+' source example"','author: Source Team','updated: 2026-11-16','reference: https://example.test/articles/'+w+'/source/'+n,'ready: true','---','']
    parts += ['# '+w.title()+' documentation','']
    for s in range(sections):parts += ['## '+w+' section '+str(s+1),'',replace(PARAGRAPHS[(layout+s)%8]),'']
    parts += ['['+w+'-api]: https://example.test/api/'+w+' "API reference"','['+w+'-home]: https://example.test/'+w,'']
    if v%4==0:parts += ['<img alt="'+w+'" width="'+n+'" src="https://example.test/images/'+w+'.svg" />','']
    if v%5==1:parts += ['> A **'+w+' note** with a wrapped line.','> Keep `inline code` and [links](https://example.test) original.','']
    if v%6==2:parts += ['| Source | State |','| :--- | ---: |','| '+w+' | **ready** |','| `item` | pending |','']
    if v%7==3:parts += ['- [x] Review '+w,'- [ ] Keep the next source','']
    lang=['json','js','python','xml'][v%4]
    body={'json':'{"name":"'+w+'","count":'+n+'}', 'js':'const '+w+' = "'+w+'";\nconsole.log('+w+');', 'python':'def '+w+'(value):\n    return value + '+n, 'xml':'<item name="'+w+'">Original &amp; source</item>'}[lang]
    parts += ['```'+lang,body,'```','','Final '+w+' paragraph with another `value` and ordinary text.']
    source='\n'.join(parts)+'\n'
    if v%4==3:source=source.replace('\n','\r\n')
    if v%11==4:source='\ufeff'+source
    label(source=source);raw=source.encode();p=root/family/f'{v:02}.md';p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve prior mixed Markdown task')
    if not p.exists():p.write_bytes(raw)
    files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original mixed Markdown tasks authored for Neural Semantic Highlighting.\nPrivate development data; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve original mixed license')
 p.write_bytes(license);lock=dict(format='nsh-markdown-mixed-v1',generatorSha256=file_hash(Path(__file__)),families=24,files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve prior mixed Markdown lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'original tasks in 24 mixed prose families')
if __name__=='__main__':main()
