"""Original opaque-content tasks; never read Golden, displays or natural holdouts."""
from pathlib import Path
import hashlib
import json
import shutil
from xml.sax.saxutils import escape, quoteattr
from training.shared.spec import PackSpec, file_hash
from packs.xml.labeling.label import label


def main():
    spec=PackSpec.open('xml');config=spec.directory/'dataset'
    history=config/'history/pre-opacity-quality-20261119';history.mkdir(parents=True,exist_ok=True)
    for name in ['sources.json','split-groups.json']:
        if not(history/name).exists():shutil.copyfile(config/name,history/name)
    sources=json.loads((history/'sources.json').read_text());groups=json.loads((history/'split-groups.json').read_text())
    source_id='xml-opacity-quality-v2';families=[f'{role}-depth-{depth}'for role in ['comment','cdata','attribute']for depth in range(8)]
    folds={source_id+':'+family:('validation'if i%6==0 else'test'if i%6==1 else'train')for i,family in enumerate(families)}
    protocol=dict(format='nsh-xml-opacity-quality-v1',families=folds,variants=24,
        purpose='Original long comments, opaque CDATA and quoted attributes; natural data/Gold/folds unchanged')
    p=config/'opacity-quality-protocol.json'
    if p.exists()and json.loads(p.read_text())!=protocol:raise ValueError('Preserve XML quality protocol')
    p.write_text(json.dumps(protocol,indent=2)+'\n');groups['assignments'].update(folds)
    folder=spec.dataset_root/'sources/opacity-quality-20261119';hashes={};files={'xml':[],'svg':[]}
    words=['sprout','canyon','meadow','harbor','comet','willow','pebble','marsh']
    for i,family in enumerate(families):
        role=family.split('-')[0];depth=int(family.rsplit('-',1)[1])
        for variant in range(24):
            word=words[(i+variant)%len(words)]
            atom=f'{word} node{variant}: if (ready < {variant+3}) {{ sample("<item data=\'plain\'>"); }} & symbolic text; '
            size=[40,120,240,400,620,980,1600,2400][variant%8]
            content=(atom*((size+len(atom)-1)//len(atom)))[:size]
            if variant%3==0:content='\n'.join(content[x:x+63]for x in range(0,len(content),63))
            if role=='comment':inner='<!-- '+content+' -->\n<tail active="true">ready &amp; waiting</tail>'
            elif role=='cdata':inner='<literal><![CDATA['+content+']]></literal>\n<tail>ready</tail>'
            else:inner='<entry description='+quoteattr(content)+' index="'+str(variant)+'">'+escape(word)+'</entry>\n<tail>ready</tail>'
            for level in range(depth%4):inner=f'<section{level}>\n'+inner+f'\n</section{level}>'
            for kind in ['xml','svg']:
                root='svg xmlns="http://www.w3.org/2000/svg"'if kind=='svg'else'document'
                source='<?xml version="1.0"?>\n<'+root+'>\n'+inner+'\n</'+root.split()[0]+'>\n'
                if variant%4==0:source=source.replace('\n','\r\n')
                label(source=source,document_kind=kind)
                raw=source.encode();name=f'{family}/{variant:02}.{kind}';p=folder/name;p.parent.mkdir(parents=True,exist_ok=True)
                if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve original opaque-content task')
                if not p.exists():p.write_bytes(raw)
                files[kind].append(name);hashes[name]=hashlib.sha256(raw).hexdigest()
    license=b'Original XML/SVG opacity tasks authored for Neural Semantic Highlighting.\nPrivate development corpus; no natural holdout, Golden or display copies.\n'
    p=folder/'LICENSE'
    if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve license')
    if not p.exists():p.write_bytes(license)
    hashes['LICENSE']=hashlib.sha256(license).hexdigest()
    lock=dict(generatorHash=file_hash(Path(__file__)),files=hashes);p=folder/'source.lock.json'
    if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve source lock')
    if not p.exists():p.write_text(json.dumps(lock,indent=2)+'\n')
    for kind in ['xml','svg']:
        sources['sources'].append(dict(id=source_id,base='dataset',path='xml/sources/opacity-quality-20261119',
            profile=kind,documentKind=kind,stream='focus',groupBy='directory',files=files[kind],extensions=['.'+kind],maxBytes=10000,
            license='xml/sources/opacity-quality-20261119/LICENSE'))
    for name,data in [('sources',sources),('split-groups',groups)]:
        (config/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    print(sum(map(len,files.values())),'original opacity tasks; existing data preserved')


if __name__=='__main__':main()
