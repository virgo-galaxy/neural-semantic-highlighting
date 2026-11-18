"""Bounded original contexts after actual validation review; no test/Golden/display reads."""
from pathlib import Path
import hashlib,json,random
from packs.makefile.labeling.label import label
from training.shared.spec import PackSpec,file_hash


def main():
 root=PackSpec.open('makefile').dataset_root/'sources/mixed-v2';files={}
 words='beech cedar dune flax iris larch moss oak reed spruce'.split()
 for bindings in range(1,5):
  for bodies in range(1,4):
   family=f'bindings-{bindings}-bodies-{bodies}'
   for variant in range(24):
    word=words[(variant+bodies)%len(words)];number=str(random.Random(181133+variant+bindings*33+bodies*471).randrange(100,900))
    lines=['# Original '+word+' workflow','MODE?=release','ROOT:=out/'+word,'CC?=cc']
    for i in range(bindings):lines += ['ITEM_'+str(i)+'?='+word+str(i),'ITEM_'+str(i)+'+=suffix']
    lines+=['NAMES=$(wildcard input/*.c)','OBJECTS=$(NAMES:.c=.o)','PATHS=$(addprefix $(ROOT)/,$(OBJECTS))',
            '','define NOTE']
    for body in range(bodies):
     lines += ['记录 '+word+' 的原始说明 🌌 '+str(body), '# Preserved literal # and $(ITEM_'+str(body%bindings)+')',
               'This '+word+' block has '+number+' records.', 'target'+str(body)+': literal body words','']
    lines+=['endef','']
    for block in range(bodies):
     lines += [word+'-part'+str(block)+':','\t@printf \"%s\\n\" \"$(ITEM_'+str(block%bindings)+')\"','']
    lines+=['ifdef MODE','FLAGS+=-Wall','else','FLAGS+=-g','endif','export MODE','-include paths.mk','',
            '.PHONY: '+word+' report clean',word+': $(PATHS)','\t@echo "Target $@ has $^"',
            '\t$(CC) $(FLAGS) -o $@ $^','',
            'report::','\t@printf "%s\\n" "$$HOME $(ROOT)"','',
            'report::','\t@echo "$(words $(PATHS)) entries"','',
            'clean:','\t-echo '+word,'']
    if variant%3==0:lines+=['once: ; @echo '+word,'']
    if variant%4==1:lines+=['HASH=before # real Make comment','ESCAPED=one\\#two','FILES=one \\', '\ttwo','']
    if variant%5==2:lines+=['.RECIPEPREFIX = >','announce:','> @echo '+word,'']
    source='\n'.join(lines)
    if variant%4==3:source=source.replace('\n','\r\n')
    if variant%9==4:source='\ufeff'+source
    label(source=source);raw=source.encode();p=root/family/f'{variant:02}.mk';p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve original mixed tasks')
    if not p.exists():p.write_bytes(raw)
    files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license_bytes=b'Original mixed Makefile tasks for Neural Semantic Highlighting.\nPrivate development data; no upstream, Golden, visible or held-out copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license_bytes:raise ValueError('Preserve mixed license')
 p.write_bytes(license_bytes);record=dict(format='nsh-makefile-mixed-v2',generatorSha256=file_hash(Path(__file__)),families=12,files=files,licenseSha256=hashlib.sha256(license_bytes).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=record:raise ValueError('Preserve mixed lock')
 p.write_text(json.dumps(record,indent=2)+'\n');print(len(files),'original mixed tasks in 12 new structural families')


if __name__=='__main__':main()
