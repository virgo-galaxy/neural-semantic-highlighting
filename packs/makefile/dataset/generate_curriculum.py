"""Original structural Make families; no Golden, display or holdout reads."""
from pathlib import Path
import hashlib
import json
import random
from packs.makefile.labeling.label import label
from training.shared.spec import PackSpec,file_hash


def main():
    root=PackSpec.open('makefile').dataset_root/'sources/curriculum-v1';files={}
    words='amber birch coral dune elm fern grove harbor iris jade kelp lotus'.split()
    for blocks in range(1,5):
        for bindings in range(1,7):
            family=f'blocks-{blocks}-bindings-{bindings}'
            for variant in range(24):
                rng=random.Random(181117+blocks*911+bindings*53+variant)
                word=words[(variant+bindings)%len(words)];number=str(rng.randrange(100,990))
                lines=['# Original '+word+' build source','CC ?= cc','MODE ?= release','ROOT := out/'+word,
                       'SRC := $(wildcard src/*.c)','OBJ := $(patsubst src/%.c,$(ROOT)/%.o,$(SRC))','-include local.mk','export MODE','']
                for i in range(bindings):lines+=['VALUE_'+str(i)+' '+['=',':=','?=','+=','::='][variant%5]+' '+word+str(i)]
                lines+=['','ifeq ($(MODE),debug)','FLAGS += -g -O0','else','FLAGS += -O2 # original choice','endif',
                        '','define NOTICE','Original '+word+' build message '+number,'# Literal $(ROOT) remains definition text','endef','']
                goals=[]
                for block in range(blocks):
                    goal=word+str(block);goals.append(goal)
                    lines += [goal+': $(OBJ) | $(ROOT)', '\t@printf "%s\\n" "Building $@"',
                              '\t$(CC) $(FLAGS) -o $@ $^','']
                    if (variant+block)%3==0:
                        lines+=['check-'+goal+':','\t@for item in one two; do \\', '\t  printf "%s\\n" "$$item"; \\', '\tdone','']
                    elif (variant+block)%3==1:
                        lines+=['check-'+goal+': ; @echo '+word,'']
                    else:lines+=['check-'+goal+':','\t-printf "%s\\n" "'+word+'"','']
                lines+=['.PHONY: '+' '.join(goals)+' clean','$(ROOT):','\tmkdir -p $@','',
                        '$(ROOT)/%.o: src/%.c | $(ROOT)','\t$(CC) $(FLAGS) -c $< -o $@','',
                        'clean:','\trm -rf $(ROOT)','']
                if variant%7==0:lines+=['STAMP := $(shell printf "%s" '+number+')','']
                if variant%4==1:lines+=['FILES = first.c \\', '\tsecond.c # a Make continuation','']
                if variant%8==3:lines+=['.RECIPEPREFIX = >','report:','> @echo '+word,'']
                source='\n'.join(lines)
                if variant%6==2:source=source.replace('Original '+word,'原始 🌌 '+word)
                if variant%4==3:source=source.replace('\n','\r\n')
                if variant%11==4:source='\ufeff'+source
                label(source=source)
                raw=source.encode();p=root/family/f'{variant:02}.mk';p.parent.mkdir(parents=True,exist_ok=True)
                if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve previous original Make tasks')
                if not p.exists():p.write_bytes(raw)
                files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
    license_bytes=b'Original Makefile tasks authored for Neural Semantic Highlighting.\nPrivate development data; no upstream, Golden or display copies.\n'
    p=root/'LICENSE'
    if p.exists()and p.read_bytes()!=license_bytes:raise ValueError('Preserve task license')
    p.write_bytes(license_bytes)
    lock=dict(format='nsh-makefile-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=24,files=files,licenseSha256=hashlib.sha256(license_bytes).hexdigest());p=root/'source.lock.json'
    if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve curriculum lock')
    p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'original Make tasks in 24 structural families')


if __name__=='__main__':main()
