"""Training-only CMD case/comment-style projections with original family folds."""
from pathlib import Path
from collections import defaultdict
import argparse
import hashlib
import json
import re
import shutil

from training.shared.spec import PackSpec, file_hash


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,required=True)
    args=parser.parse_args();spec=PackSpec.open('bat');config=spec.directory/'dataset'
    history=config/'history/pre-case-quality-20261119';history.mkdir(parents=True,exist_ok=True)
    for name in ['sources.json','split-groups.json']:
        if not(history/name).exists():shutil.copyfile(config/name,history/name)
    sources=json.loads((history/'sources.json').read_text());groups=json.loads((history/'split-groups.json').read_text())
    entries=defaultdict(list);derivations=[]
    for d in map(json.loads,(args.snapshot/'train/documents.jsonl').read_text().splitlines()):
        if d['stream']!='natural':continue
        repository,family=d['sourceGroup'].split(':',1)
        if groups['assignments'][d['sourceGroup']]!='train':raise ValueError('Projection would cross a frozen holdout')
        upper=d['source'].translate(str.maketrans('abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        lower=d['source'].translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))
        comments=re.sub(r'(?im)^([ \t]*)(?:@?rem\b|::)',lambda m:m[1]+'@REM',upper)
        for style,source in [('upper',upper),('lower',lower),('at-rem',comments)]:
            relative=d['id'][:16]+'/'+style+'.cmd'
            root=spec.dataset_root/'sources/case-quality-20261119'/repository;path=root/relative;raw=source.encode('utf-8')
            path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists()and path.read_bytes()!=raw:raise ValueError('Preserve previous focus projection')
            if not path.exists():path.write_bytes(raw)
            entries[repository].append((relative,family))
            derivations.append(dict(repository=repository,path=relative,sourceGroup=d['sourceGroup'],stream='focus',
                originalPath=d['path'],originalSourceHash=d['contentHash'],transformation=style,sha256=hashlib.sha256(raw).hexdigest()))
    for repository,files in entries.items():
        original=next(e for e in sources['sources']if e['id']==repository and e.get('stream','natural')=='natural')
        sources['sources'].append(dict(id=repository,base='dataset',path='bat/sources/case-quality-20261119/'+repository,
            profile='bat',stream='focus',extensions=['.cmd'],files=[n for n,_ in files],groups=dict(files),
            maxBytes=40000,license=original['license']))
    (config/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
    protocol=dict(format='nsh-bat-case-quality-v1',snapshot=str(args.snapshot),
        snapshotManifestHash=file_hash(args.snapshot/'manifest.json'),generatorHash=file_hash(Path(__file__)),
        rule='Only natural TRAIN originals; derivative remains focus in its original source family; no validation/test projection',
        derivations=derivations)
    (config/'case-quality-protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    print(len(derivations),'training-only case/comment projections',flush=True)


if __name__=='__main__':main()
