"""Original mixed metadata contexts; avoid header-only cross-family copy exclusions."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash
from .generate_curriculum import task,unified,WORDS

def main():
 root=PackSpec.open('diff').dataset_root/'sources/curriculum-metadata-v1';files={}
 for kind in ['rename','copy','mode','binary']:
  for layout in ['before','after','unicode','spacing']:
   family=kind+'-'+layout
   for v in range(20):
    w=WORDS[v%len(WORDS)];prefix=kind+'_'+layout+'_'+w
    body=unified(prefix+'/details.txt',['Original '+prefix],['Updated '+prefix],['Shared original source'],git=True);meta=task(kind,w,v);source=(body+meta)if layout=='after'else meta+body
    if layout=='unicode':source=source.replace('Original '+prefix,'Original 星空 🌌 '+prefix).replace('Updated '+prefix,'Updated 宇宙 👩🏽‍💻 '+prefix)
    if layout=='spacing':source=source.replace('Original '+prefix,'Original  '+prefix+'\t').replace('Updated '+prefix,'Updated\t'+prefix+'  ')
    if kind!='binary'and v%4==1:source=source.replace('\n','\r\n')
    raw=source.encode();p=root/family/f'{v:02}.diff';p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve original metadata context')
    if not p.exists():p.write_bytes(raw)
    files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original mixed Diff metadata contexts for Neural Semantic Highlighting.\nNo Golden, display or upstream source copying.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve license')
 p.write_bytes(license);lock=dict(format='nsh-diff-metadata-curriculum-v1',generatorSha256=file_hash(Path(__file__)),baseGeneratorSha256=file_hash(Path(__file__).with_name('generate_curriculum.py')),families=16,files=files);p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve metadata lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'original metadata contexts')
if __name__=='__main__':main()
