"""Capture additional existing Perl core families without executing modules."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import shutil

from training.shared.spec import PackSpec, file_hash


def main():
    spec=PackSpec.open('perl');config=spec.directory/'dataset'
    history=config/'history/pre-quality-20261119';history.mkdir(parents=True,exist_ok=True)
    for name in ['sources.json','split-groups.json']:
        if not(history/name).exists():shutil.copyfile(config/name,history/name)
    sources=json.loads((history/'sources.json').read_text())
    groups=json.loads((history/'split-groups.json').read_text())
    original=sources['sources'][0];seen=set(original['files'])
    host=Path('/System/Library/Perl/5.34');families=defaultdict(list)
    for path in host.rglob('*.pm'):
        relative=path.relative_to(host);name=str(relative)
        if (name in seen or not 600<path.stat().st_size<25000 or
                set(relative.parts)&{'auto','CORE','unicore','CPAN','Test','Test2'}):continue
        family=relative.parts[0]if len(relative.parts)>1 else path.stem
        families[family].append(name)
    chosen=[];mapping={};fresh={'validation':[],'test':[]}
    for family,names in sorted(families.items()):
        group=original['id']+':'+family
        if group not in groups['assignments']:
            bucket=int(hashlib.sha256(('quality-perl:'+family).encode()).hexdigest()[:8],16)%10
            split='validation'if bucket==0 else'test'if bucket==1 else'train'
            groups['assignments'][group]=split
            if split in fresh:fresh[split].append(group)
        selected=sorted(names,key=lambda n:hashlib.sha256(n.encode()).hexdigest())[:3]
        chosen+=selected;mapping.update({n:family for n in selected})
    # The paths/folds are now frozen before reading any new source contents.
    protocol=dict(format='nsh-perl-quality-protocol-v1',metadataSelection='At most three modules per top-level namespace; fixed path hash folds',
        freshValidationSourceGroups=fresh['validation'],freshTestSourceGroups=fresh['test'],files=chosen)
    (config/'quality-protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    root=spec.dataset_root/'sources/core-quality-20261119';files={}
    for name in chosen:
        raw=(host/name).read_bytes();raw.decode('utf-8');target=root/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists()and target.read_bytes()!=raw:raise ValueError('Preserve core source capture')
        if not target.exists():target.write_bytes(raw)
        files[name]=hashlib.sha256(raw).hexdigest()
    license=b'This original Perl core capture retains the complete Perl Artistic/GPL license texts.\n'
    for name in ['perlartistic.pod','perlgpl.pod']:
        raw=(host/'pods'/name).read_bytes();target=root/'licenses'/name;target.parent.mkdir(exist_ok=True)
        if target.exists()and target.read_bytes()!=raw:raise ValueError('Preserve original license')
        if not target.exists():target.write_bytes(raw)
        files['licenses/'+name]=hashlib.sha256(raw).hexdigest();license+=b'\n'+raw
    target=root/'LICENSE'
    if target.exists()and target.read_bytes()!=license:raise ValueError('Preserve license bundle')
    if not target.exists():target.write_bytes(license)
    files['LICENSE']=hashlib.sha256(license).hexdigest()
    lock=dict(origin=str(host),collectorHash=file_hash(Path(__file__)),files=files)
    target=root/'source.lock.json'
    if target.exists()and json.loads(target.read_text())!=lock:raise ValueError('Preserve immutable source lock')
    if not target.exists():target.write_text(json.dumps(lock,indent=2)+'\n')
    sources['sources'].append(dict(id=original['id'],base='dataset',path='perl/sources/core-quality-20261119',
        profile='perl5',extensions=['.pm'],files=chosen,groups=mapping,maxBytes=25000,
        license='perl/sources/core-quality-20261119/LICENSE'))
    for name,data in [('sources',sources),('split-groups',groups)]:
        (config/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    print(len(chosen),'additional modules; original namespace folds retained',flush=True)


if __name__=='__main__':main()
