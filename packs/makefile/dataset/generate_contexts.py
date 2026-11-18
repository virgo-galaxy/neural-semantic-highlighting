"""Original contrasting Make contexts from validation categories; no source/Golden/test reads."""
from pathlib import Path
import hashlib,json,random
from packs.makefile.labeling.label import label
from training.shared.spec import PackSpec,file_hash


def main():
 root=PackSpec.open('makefile').dataset_root/'sources/contexts-v1';files={};words='alder bay cedar dune elm flax grove iris larch moss oak reed'.split()
 for bindings in range(1,5):
  for blocks in range(1,5):
   family=f'bindings-{bindings}-rules-{blocks}'
   for variant in range(20):
    word=words[(bindings+variant)%len(words)];width=48+(variant%5)*8;banner='# '+'#'*width
    lines=[banner,'# Original '+word+' build notes; source only.','# Copyright example authors; original development task.',banner,'','CC?=cc','OUT:=build/'+word,'SRC=$(wildcard code/*.c)','OBJ=$(SRC:code/%.c=$(OUT)/%.o)','']
    for i in range(bindings):
     lines += ['VALUE_'+str(i)+['=','?=','+=',':='][variant%4]+word+str(i),'FLAGS_'+str(i)+' += -Wall -Wextra -I$(OUT)/include -DNAME='+word]
    lines += ['FILES=first.c \\', '      second.c \\', '\tthird.c','',
              'define DOCUMENT','Release information for '+word+'.','# Literal $(VALUE_0) and rule: syntax stay definition text.', 'The '+word+' record remains original.','endef','']
    for block in range(blocks):
     goal=word+'-'+str(block);spaces=' '*(10+(variant%4)*7)
     lines += [banner,'# Build section '+str(block),banner,goal+': $(OBJ) | $(OUT)',
               '\t@printf "%s\\n" "  '+goal+spaces+'compile source files"',
               '\t@printf "%s\\n" "  docs'+spaces+'generate local documentation"',
               '\t@echo "Use \\`make '+goal+"' to display original help text\"",
               '\t$(CC) $(FLAGS_0) -I$(OUT)/include -c $< -o $@',
               '\t@for name in alpha beta; do \\', '\t  printf "%s\\n" "$$name $(OUT)"; \\', '\tdone','']
     if variant%3==1:lines += [goal+'-extra::','\t@echo "$(words $(OBJ)) files; $$HOME"','']
    lines += ['.PHONY: clean show','$(OUT):','\tmkdir -p $@','',
              'show:','\t@printf "%s\\n" "$(addprefix result/,$(SRC:.c=.o))"','',
              'clean:','\t-rm -rf $(OUT)','']
    if variant%4==2:lines+=['VERSION := $(shell printf "%s" '+str(random.Random(bindings*91+blocks*31+variant).randrange(200,900))+')','']
    if variant%5==3:lines+=['ifdef DEBUG','TRACE?=enabled','else','TRACE?=disabled','endif','']
    source='\n'.join(lines)
    if variant%6==3:source=source.replace('Original '+word,'原文 🌌 '+word)
    if variant%4==1:source=source.replace('\n','\r\n')
    if variant%9==4:source='\ufeff'+source
    label(source=source);raw=source.encode();p=root/family/f'{variant:02}.mk';p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve previous original contexts')
    if not p.exists():p.write_bytes(raw)
    files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license_bytes=b'Original Makefile context tasks for Neural Semantic Highlighting.\nPrivate development data; no copied upstream, Golden, display or test source.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license_bytes:raise ValueError('Preserve task license')
 p.write_bytes(license_bytes);record=dict(format='nsh-makefile-contexts-v1',generatorSha256=file_hash(Path(__file__)),families=16,files=files,licenseSha256=hashlib.sha256(license_bytes).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=record:raise ValueError('Preserve context lock')
 p.write_text(json.dumps(record,indent=2)+'\n');print(len(files),'original context tasks in 16 structural families')


if __name__=='__main__':main()
