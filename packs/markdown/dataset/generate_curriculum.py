"""Original Markdown structural families; never reads Golden or display sources."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
WORDS='aspen brook cypress delta elm forest glade heath island juniper kelp lotus mist north ocean pine quartz reed sage thyme'.split()
CODE={
 'js':'const @W@ = { title: "@W@", count: @N@ };\nconsole.log(@W@.title);',
 'tsx':'export function @W@() {\n  return <section data-count={@N@}>@W@</section>;\n}',
 'python':'def @W@(count):\n    return [value * @N@ for value in range(count)]\n\nprint(@W@(3))',
 'sh':'function @W@() {\n  printf "Processed %s files\\n" "$1"\n}\n@W@ @N@',
 'json':'{"name":"@W@","count":@N@,"ready":true}',
 'yaml':'name: @W@\ncount: @N@\nready: true',
 'css':'.@W@ {\n  display: grid;\n  gap: @N@px;\n}',
 'xml':'<record name="@W@"><count>@N@</count></record>',
 'go':'package main\n\nfunc @W@(n int) int {\n  return n + @N@\n}',
 'unknown-example':'Original @W@ source with @N@ values; no language detection.'}
def main():
 from packs.markdown.labeling.label import label
 root=PackSpec.open('markdown').dataset_root/'sources/curriculum-v1';files={}
 for depth in range(1,6):
  for items in range(1,9):
   family=f'sections-{depth}-{items}'
   for v in range(24):
    w=WORDS[(depth*7+items+v)%len(WORDS)];n=random.Random(2871+depth*71+items*41+v).randrange(4,90);parts=[]
    if v%7==0:parts+=['---','title: '+w,'ready: true','---','']
    for d in range(depth):
     parts+=['#'*(d+1)+' '+w.title()+' '+str(d),'',f'Original **{w} text** with *clear emphasis*, ~~previous wording~~ and `value_{n}`.','']
    parts+=[f'Read the [{w} guide](https://example.test/{w} "Guide") and keep &amp; references original.','']
    for j in range(items):
     bullet=str(j+1)+'.'if v%3==1 else '-'
     task=('[x] 'if j%2 else'[ ] ')if v%3==2 else''
     parts+=[f'{bullet} {task}Review {w} item {j+1} with **{n+j} details**.']
    # All structural families contain tasks, while the variable list keeps shape distinct.
    parts+=['','- [x] Prepare original samples','- [ ] Inspect the next result','',f'> A {w} note with *emphasis*.','>','> Keep the source and line endings.','','| Name | Count |','| :--- | ---: |',f'| **{w}** | `{n}` |','| [reference](https://example.test) | ready |','']
    lang=list(CODE)[v%len(CODE)];body=CODE[lang].replace('@W@',w).replace('@N@',str(n));fence='~~~'if v%4==1 else'```'
    info=lang+(' title='+w+'.source'if v%5==2 else'')
    parts += [fence+info,body]
    if v%11!=9:parts += [fence,'',f'<!-- Original {w} comment -->','',f'Closing paragraph for {w} with \\*literal markers\\*.']
    source='\n'.join(parts)+'\n'
    if v%4==3:source=source.replace('\n','\r\n')
    if v%13==4:source='\ufeff'+source
    label(source=source);raw=source.encode();p=root/family/f'{v:02}.md';p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve existing Markdown curriculum')
    if not p.exists():p.write_bytes(raw)
    files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original Markdown tasks authored for Neural Semantic Highlighting.\nPrivate development data; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve original Markdown license')
 p.write_bytes(license);lock=dict(format='nsh-markdown-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=40,files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve existing Markdown source lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'original Markdown tasks in 40 structural families')
if __name__=='__main__':main()
