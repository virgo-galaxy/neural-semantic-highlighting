"""Original Dockerfile families. Never read Golden, displays or natural holdouts."""
from pathlib import Path
import hashlib
import json
import random

from packs.dockerfile.labeling.label import label
from training.shared.spec import PackSpec, file_hash


def main():
    root=PackSpec.open('dockerfile').dataset_root/'sources/curriculum-v1'
    files={};words='amber birch coral delta elm fern grove harbor iris jade kelp lotus'.split()
    for stages in range(1,4):
        for steps in range(1,9):
            family=f'stages-{stages}-steps-{steps}'
            for variant in range(24):
                rng=random.Random(170517+stages*911+steps*53+variant)
                word=words[(variant+steps)%len(words)];number=str(rng.randrange(1200,9800))
                parts=['# syntax=docker/dockerfile:1','# Original '+word+' container source','ARG BASE=alpine:3','ARG TARGETPLATFORM=linux/amd64']
                for stage in range(stages):
                    base='${BASE}' if variant%2 else ['alpine:3','node:lts-alpine','python:3-slim'][variant%3]
                    parts+=['','FROM --platform=$TARGETPLATFORM '+base+' AS '+word+str(stage),
                            'ARG CHANNEL=stable','ENV APP='+word+' COUNT='+number+' NOTE="original # literal"',
                            'LABEL org.example.name="'+word+'" org.example.stage="'+str(stage)+'"',
                            'WORKDIR /srv/${APP}','COPY --chown=1000:1000 ./source/ ./']
                    if stage:parts+=['COPY --from='+word+str(stage-1)+' /srv/output /srv/previous']
                    for step in range(steps):
                        if (variant+step)%4==0:parts+=['RUN ["printf", "%s", "'+word+'-'+str(step)+'"]']
                        elif (variant+step)%4==1:parts+=['RUN --mount=type=cache,target=/tmp/'+word+' \\', '    # Original continuation comment','    mkdir -p /tmp/'+word+' && printf "%s\\n" "'+word+'"']
                        elif (variant+step)%4==2:parts+=['RUN value='+number+'; printf "%s\\n" "$value"']
                        else:parts+=['RUN echo '+word+' && test -d /srv']
                    delimiter='SOURCE_'+str(stage)
                    parts+=['COPY <<\''+delimiter+'\' /etc/'+word+'.conf','name='+word,'','count='+number,
                            '# Literal FROM/RUN words stay file content',delimiter,
                            'RUN <<SCRIPT_'+str(stage),'set -eu','echo '+word,'','printf "%s\\n" "$CHANNEL"','SCRIPT_'+str(stage)]
                if variant%5==0:parts+=['SHELL ["/bin/bash", "-eu", "-c"]','RUN echo ready']
                if variant%7==0:parts+=['ONBUILD COPY --chown=1000:1000 ["assets", "/srv/assets"]']
                parts+=['EXPOSE '+number+' 8080/tcp','VOLUME ["/srv/data", "/srv/cache"]',
                        'HEALTHCHECK --interval=25s --timeout=3s CMD test -d /srv || exit 1',
                        'STOPSIGNAL SIGTERM','USER 1000:1000','ENTRYPOINT ["/bin/sh", "-c"]','CMD ["echo original '+word+'"]']
                source='\n'.join(parts)+'\n'
                if variant%4==3:source=source.replace('\n','\r\n')
                if variant%11==4:source='\ufeff'+source
                if variant%6==2:source=source.replace('original '+word,'原文 🌌 '+word)
                label(source=source)
                raw=source.encode('utf-8');path=root/family/f'{variant:02}.dockerfile';path.parent.mkdir(parents=True,exist_ok=True)
                if path.exists()and path.read_bytes()!=raw:raise ValueError('Preserve original Dockerfile task')
                if not path.exists():path.write_bytes(raw)
                files[str(path.relative_to(root))]=hashlib.sha256(raw).hexdigest()
    license_bytes=b'Original Dockerfile tasks authored for Neural Semantic Highlighting.\nPrivate development data; no upstream, Golden or display copies.\n'
    path=root/'LICENSE'
    if path.exists()and path.read_bytes()!=license_bytes:raise ValueError('Preserve original task license')
    path.write_bytes(license_bytes)
    record=dict(format='nsh-dockerfile-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=24,files=files,licenseSha256=hashlib.sha256(license_bytes).hexdigest())
    path=root/'source.lock.json'
    if path.exists()and json.loads(path.read_text())!=record:raise ValueError('Preserve previous Dockerfile curriculum lock')
    path.write_text(json.dumps(record,indent=2)+'\n');print(len(files),'original Dockerfile tasks in 24 structural families')


if __name__=='__main__':main()
