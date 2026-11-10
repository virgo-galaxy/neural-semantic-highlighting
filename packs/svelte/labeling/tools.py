"""Pinned, parse-only Svelte bundle; uses existing Node without an installation."""
from __future__ import annotations
import base64,hashlib,json,subprocess,tarfile
from functools import lru_cache
from pathlib import Path
from training.shared.spec import REPOSITORY,file_hash

CONFIG=Path(__file__).with_name('tools.json')
DIRECTORY=REPOSITORY/'artifacts/tools/svelte-gold/svelte-5.38.0'

def fetch():
    config=json.loads(CONFIG.read_text());archive=REPOSITORY/'artifacts/cache/gold-tools/svelte-5.38.0.tgz'
    archive.parent.mkdir(parents=True,exist_ok=True)
    if not archive.exists():
        raw=subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--http1.1','--retry','3',config['url']])
    else:raw=archive.read_bytes()
    if hashlib.sha1(raw).hexdigest()!=config['sha1'] or 'sha512-'+base64.b64encode(hashlib.sha512(raw).digest()).decode()!=config['integrity']:raise ValueError('Official Svelte archive differs')
    if not archive.exists():archive.write_bytes(raw)
    sources={}
    with tarfile.open(archive) as bundle:
        for name in config['files']:
            member=bundle.getmember('package/'+name)
            if not member.isfile():raise ValueError('Expected original compiler file')
            raw=bundle.extractfile(member).read();path=DIRECTORY/name
            if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve existing compiler bundle')
            path.parent.mkdir(parents=True,exist_ok=True)
            if not path.exists():path.write_bytes(raw)
            sources[name]=hashlib.sha256(raw).hexdigest()
    lock=dict(format='nsh-svelte-gold-tools-lock-v1',configSha256=file_hash(CONFIG),sources=sources)
    path=DIRECTORY/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Preserve previous compiler lock')
    path.write_text(json.dumps(lock,indent=2)+'\n');print('Offline Svelte parser:',DIRECTORY)

@lru_cache(maxsize=1)
def provenance():
    lock=json.loads((DIRECTORY/'source.lock.json').read_text())
    if lock['configSha256']!=file_hash(CONFIG):raise ValueError('Compiler config changed')
    for name,expected in lock['sources'].items():
        if file_hash(DIRECTORY/name)!=expected:raise ValueError('Compiler bundle differs')
    node=Path(subprocess.check_output(['node','-p','process.execPath'],text=True).strip())
    dependencies=[Path(__file__).with_name('teacher.mjs'),REPOSITORY/'pnpm-lock.yaml',REPOSITORY/'node_modules/entities/package.json']
    dependencies+=sorted((REPOSITORY/'node_modules/entities/dist').rglob('*.js'))
    return dict(name='Official Svelte parse-only teacher',version='5.38.0',**lock,nodeVersion=subprocess.check_output([str(node),'--version'],text=True).strip(),nodeSha256=file_hash(node),dependencies={str(p.relative_to(REPOSITORY)):file_hash(p) for p in dependencies},sdkRequired=False)

if __name__=='__main__':fetch()
