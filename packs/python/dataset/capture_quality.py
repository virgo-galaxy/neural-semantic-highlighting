"""Bounded existing stdlib/package source capture; never import collected modules."""
from pathlib import Path
from collections import defaultdict
import hashlib
import importlib.metadata
import json
import shutil

from training.shared.spec import PackSpec, file_hash


def main():
    spec=PackSpec.open('python');config=spec.directory/'dataset'
    history=config/'history/pre-quality-20261119';history.mkdir(parents=True,exist_ok=True)
    for name in ['sources.json','split-groups.json']:
        if not(history/name).exists():shutil.copyfile(config/name,history/name)
    sources=json.loads((history/'sources.json').read_text());groups=json.loads((history/'split-groups.json').read_text())
    original=sources['sources'][0];seen=set(original['files'])
    stdlib=Path('artifacts/tools/python/cpython-3.15.0-macos-aarch64-none/lib/python3.15').resolve()
    packages=[dict(id=original['id'],origin=stdlib,root=stdlib,license=stdlib/'LICENSE.txt',version='existing CPython 3.15.0',limit=96)]
    for name,limit in [('networkx',24),('filelock',12),('jinja2',8)]:
        distribution=importlib.metadata.distribution(name)
        license=next(p for p in distribution.files if '.dist-info/'in str(p)and p.name.upper().startswith('LICENSE'))
        root=Path(distribution.locate_file(name)).resolve()
        packages.append(dict(id='python-quality-'+name,origin=root,root=root,license=Path(distribution.locate_file(license)),version=distribution.version,limit=limit,projectTest=name=='jinja2'))
    selections=[];plans=[];fresh={'validation':[],'test':[]}
    denied={'test','tests','__pycache__','site-packages','idlelib','ensurepip','turtledemo','encodings','pydoc_data'}
    for package in packages:
        families=defaultdict(list);root=package['root']
        for path in root.rglob('*.py'):
            relative=path.relative_to(root);name=str(relative)
            if (set(relative.parts)&denied or not 300<path.stat().st_size<25000 or
                package['id']==original['id']and name in seen):continue
            if package['id']==original['id']:
                family=relative.parts[0]if len(relative.parts)>1 else path.stem
                family={'abc':'_py_abc','ntpath':'posixpath','cProfile':'profiling','profile':'profiling'}.get(family,family)
            elif package['id'].endswith('filelock')or package.get('projectTest'):family='project'
            else:family='/'.join(relative.parts[:2])if len(relative.parts)>2 else relative.parts[0]if len(relative.parts)>1 else path.stem
            families[family].append(name)
        chosen=[];mapping={};folds={}
        for family,names in sorted(families.items(),key=lambda row:hashlib.sha256((package['id']+row[0]).encode()).hexdigest()):
            group=package['id']+':'+family
            if group in groups['assignments']:split=groups['assignments'][group]
            elif package.get('projectTest'):split='test'
            elif package['id'].endswith('filelock'):split='train'
            else:
                bucket=int(hashlib.sha256(('quality-python:'+group).encode()).hexdigest()[:8],16)%10
                split='validation'if bucket==0 else'test'if bucket==1 else'train'
            per_family=package['limit']if family=='project'else 3
            selected=sorted(names,key=lambda n:hashlib.sha256(n.encode()).hexdigest())[:per_family]
            if len(chosen)+len(selected)>package['limit']:continue
            chosen+=selected;mapping.update({n:family for n in selected});folds[group]=split
            if group not in groups['assignments']and split in fresh:fresh[split].append(group)
            groups['assignments'][group]=split
        folder='quality-'+package['id']+'-'+package['version'].replace(' ','-')+'-20261119'
        plans.append(dict(package=package,files=chosen,groups=mapping,folder=folder))
        selections.append(dict(id=package['id'],version=package['version'],origin=str(root),folder=folder,files=chosen,folds=folds))
    # Freeze all paths and family folds before reading any new source content.
    protocol=dict(format='nsh-python-quality-protocol-v1',sources=selections,
        freshValidationSourceGroups=fresh['validation'],freshTestSourceGroups=fresh['test'],
        scope='Existing CPython plus installed package files; no installs, module imports or source execution; Jinja2 project held out')
    (config/'quality-protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    for plan in plans:
        package=plan['package'];folder=spec.dataset_root/'sources'/plan['folder'];files={}
        for name in plan['files']:
            raw=(package['root']/name).read_bytes();raw.decode('utf-8');target=folder/name
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists()and target.read_bytes()!=raw:raise ValueError('Preserve original source capture')
            if not target.exists():target.write_bytes(raw)
            files[name]=hashlib.sha256(raw).hexdigest()
        raw=package['license'].read_bytes();raw.decode('utf-8');target=folder/'LICENSE'
        if target.exists()and target.read_bytes()!=raw:raise ValueError('Preserve original license')
        if not target.exists():target.write_bytes(raw)
        files['LICENSE']=hashlib.sha256(raw).hexdigest()
        lock=dict(origin=str(package['origin']),version=package['version'],collectorHash=file_hash(Path(__file__)),files=files)
        target=folder/'source.lock.json'
        if target.exists()and json.loads(target.read_text())!=lock:raise ValueError('Preserve source lock')
        if not target.exists():target.write_text(json.dumps(lock,indent=2)+'\n')
        sources['sources'].append(dict(id=package['id'],base='dataset',path='python/sources/'+plan['folder'],profile='python3',documentKind='python',
            extensions=['.py'],files=plan['files'],groups=plan['groups'],maxBytes=25000,license='python/sources/'+plan['folder']+'/LICENSE'))
    for name,data in [('sources',sources),('split-groups',groups)]:
        (config/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    print([(x['id'],len(x['files']))for x in selections],flush=True)


if __name__=='__main__':main()
