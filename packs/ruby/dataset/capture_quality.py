"""Capture bounded additional files at the existing pinned Ruby project revisions."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import quote
from training.shared.spec import PackSpec, file_hash


def fetch(url):
    return subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--http1.1','--retry','3','--retry-all-errors',url])


def main():
    spec=PackSpec.open('ruby');config=spec.directory/'dataset';history=config/'history/pre-quality-20261119'
    history.mkdir(parents=True,exist_ok=True)
    for name in ['sources.json','split-groups.json']:
        if not(history/name).exists():shutil.copyfile(config/name,history/name)
    sources=json.loads((history/'sources.json').read_text());groups=json.loads((history/'split-groups.json').read_text())
    upstreams=json.loads((config/'upstreams.json').read_text())['upstreams'];plans=[]
    for upstream in upstreams:
        entry=next(x for x in sources['sources']if x['id']==upstream['id']);seen=set(entry['files'])
        def family(name):
            relative=name.split('/lib/',1)[-1]if '/lib/'in name else name.removeprefix('lib/')
            path=Path(relative)
            return str(path.parent)+':'+path.stem.split('_')[0].split('-')[0]
        if any(family(name)!=group for name,group in entry['groups'].items()):raise ValueError('Original Ruby family convention changed')
        cache=spec.dataset_root/'metadata/quality-20261119';cache.mkdir(parents=True,exist_ok=True);metadata=cache/(upstream['id']+'.json')
        if not metadata.exists():metadata.write_bytes(fetch(f"https://api.github.com/repos/{upstream['repository']}/git/trees/{upstream['revision']}?recursive=1"))
        tree=json.loads(metadata.read_text())
        if tree.get('truncated'):raise ValueError('Incomplete pinned source tree')
        candidates=[x for x in tree['tree']if x['type']=='blob'and x['path'].endswith('.rb')and('/lib/'in x['path']or x['path'].startswith('lib/'))and x['path']not in seen and 400<x.get('size',0)<18000]
        limit=32 if upstream['id'].startswith('rails')else 16 if upstream['id'].startswith('rspec')else 8
        chosen=[];per_family={}
        for item in sorted(candidates,key=lambda x:hashlib.sha256(x['path'].encode()).hexdigest()):
            group=family(item['path'])
            if per_family.get(group,0)>=2:continue
            key=entry['id']+':'+group
            if key not in groups['assignments']:
                bucket=int(hashlib.sha256(('quality-ruby:'+key).encode()).hexdigest()[:8],16)%10
                groups['assignments'][key]='validation'if bucket==0 else'test'if bucket==1 else'train'
            chosen.append(dict(path=item['path'],gitBlob=item['sha'],group=group,split=groups['assignments'][key]));per_family[group]=per_family.get(group,0)+1
            if len(chosen)>=limit:break
        plans.append(dict(id=entry['id'],repository=upstream['repository'],revision=upstream['revision'],files=chosen))
    protocol=dict(format='nsh-ruby-quality-protocol-v1',sources=plans,policy='Metadata frozen before source capture; original revisions, family function and prior folds preserved; no SDK or source execution')
    target=config/'quality-protocol.json'
    if target.exists()and json.loads(target.read_text())!=protocol:raise ValueError('Preserve Ruby quality protocol')
    target.write_text(json.dumps(protocol,indent=2)+'\n')
    for plan in plans:
        folder=spec.dataset_root/'sources/quality-20261119'/plan['id']
        def capture(item):
            name=item['path'];url=f"https://raw.githubusercontent.com/{plan['repository']}/{plan['revision']}/{quote(name,safe='/')}";path=folder/name
            raw=path.read_bytes()if path.exists()else fetch(url);raw.decode('utf-8')
            if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=item['gitBlob']:raise ValueError('Pinned Git blob mismatch')
            path.parent.mkdir(parents=True,exist_ok=True)
            if not path.exists():path.write_bytes(raw)
            return name,hashlib.sha256(raw).hexdigest()
        with ThreadPoolExecutor(max_workers=4)as pool:hashes=dict(pool.map(capture,plan['files']))
        raw=(spec.dataset_root/'sources'/plan['id']/'LICENSES.txt').read_bytes();target=folder/'LICENSES.txt'
        if target.exists()and target.read_bytes()!=raw:raise ValueError('Preserve original licensing')
        if not target.exists():target.write_bytes(raw)
        hashes['LICENSES.txt']=hashlib.sha256(raw).hexdigest();lock=dict(provenance=plan,collectorHash=file_hash(Path(__file__)),files=hashes);target=folder/'source.lock.json'
        if target.exists()and json.loads(target.read_text())!=lock:raise ValueError('Preserve immutable Ruby capture lock')
        if not target.exists():target.write_text(json.dumps(lock,indent=2)+'\n')
        sources['sources'].append(dict(id=plan['id'],base='dataset',path='ruby/sources/quality-20261119/'+plan['id'],profile='ruby',extensions=['.rb'],
            files=[x['path']for x in plan['files']],groups={x['path']:x['group']for x in plan['files']},maxBytes=18000,license='ruby/sources/quality-20261119/'+plan['id']+'/LICENSES.txt'))
    for name,data in [('sources',sources),('split-groups',groups)]:
        (config/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    print(sum(len(x['files'])for x in plans),'additional pinned Ruby files; no runtime installed')


if __name__=='__main__':main()
