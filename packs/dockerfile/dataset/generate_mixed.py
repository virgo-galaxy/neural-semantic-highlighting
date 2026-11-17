"""Original contrasts after natural validation/display review, never test reads."""
from pathlib import Path
import hashlib
import json
import random

from packs.dockerfile.labeling.label import label
from training.shared.spec import PackSpec, file_hash


def main():
    root=PackSpec.open('dockerfile').dataset_root/'sources/mixed-v1';files={}
    words='birch dune fern jade maple pearl quartz reed sage willow'.split()
    for declarations in range(1,4):
        for blocks in range(1,5):
            family=f'bindings-{declarations}-blocks-{blocks}'
            for variant in range(24):
                word=words[(variant+blocks)%len(words)];number=str(random.Random(371117+variant+blocks*41+declarations*731).randrange(2000,9200))
                parts=['# syntax=docker/dockerfile:1','# 原始容器说明 🌌 — retain comments and source','FROM '+['alpine:3','node:lts','python:3-slim'][variant%3]+' AS '+word,'']
                for index in range(declarations):parts+=['ARG ITEM_'+str(index)+'='+word,'ENV ENTRY_'+str(index)+'="'+word+' # original"']
                parts+=['WORKDIR /home/'+word,'USER '+word+':'+word,'LABEL org.example.role="'+word+'"']
                for block in range(blocks):
                    parts+=['','COPY '+word+'.json '+word+'.lock ./',
                            'COPY ["'+word+' settings.toml", "/etc/'+word+'/settings.toml"]',
                            'RUN '+['npm ci','pip install package','go build ./cmd/app','yarn install'][variant%4]+' --mode='+word+' --count='+number]
                    delimiter='ARCHIVE_'+str(block)
                    body=['记录 '+word+' 的原始文件内容 🌌。','<article title="'+word+'">Keep source &amp; text.</article>','','# Metadata-looking content is still literal.','FROM literal-image','RUN these words do not start an instruction.','name='+word,'owner="'+word+'"','The '+word+' record has '+number+' entries.']
                    if variant%3==1:body=body*2
                    parts+=['COPY <<\''+delimiter+'\' /etc/'+word+'/archive'+str(block)+'.txt',*body,delimiter]
                parts+=['','EXPOSE '+number,'STOPSIGNAL SIGTERM','CMD ["echo", "'+word+'"]']
                source='\n'.join(parts)+'\n'
                if variant%2:source=source.replace('\n','\r\n')
                if variant%3!=1:source='\ufeff'+source
                label(source=source);raw=source.encode('utf-8');path=root/family/f'{variant:02}.dockerfile';path.parent.mkdir(parents=True,exist_ok=True)
                if path.exists()and path.read_bytes()!=raw:raise ValueError('Preserve original mixed Dockerfile task')
                if not path.exists():path.write_bytes(raw)
                files[str(path.relative_to(root))]=hashlib.sha256(raw).hexdigest()
    license_bytes=b'Original mixed Dockerfile tasks for Neural Semantic Highlighting.\nPrivate development data; no upstream, Golden, display or held-out copies.\n';p=root/'LICENSE'
    if p.exists()and p.read_bytes()!=license_bytes:raise ValueError('Preserve mixed Dockerfile license')
    p.write_bytes(license_bytes);record=dict(format='nsh-dockerfile-mixed-v1',generatorSha256=file_hash(Path(__file__)),families=12,files=files,licenseSha256=hashlib.sha256(license_bytes).hexdigest());p=root/'source.lock.json'
    if p.exists()and json.loads(p.read_text())!=record:raise ValueError('Preserve mixed Dockerfile lock')
    p.write_text(json.dumps(record,indent=2)+'\n');print(len(files),'original mixed Dockerfile tasks in 12 families')


if __name__=='__main__':main()
