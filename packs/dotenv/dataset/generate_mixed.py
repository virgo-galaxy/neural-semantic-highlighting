"""Mixed dotenv quote/comment/string contexts, preserving independent layouts."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
LAYOUTS={
 'exported-empty':dict(exports=1,empty=8,keys=[0,1,2,3,4,5]),
 'exported-middle':dict(exports=12,empty=1,keys=[0,1,2,3,4,5]),
 'exported-alternate':dict(exports=21,empty=32,keys=[0,1,2,3,4,5]),
 'exported-footer':dict(exports=48,empty=4,keys=[0,1,2,3,4,5]),
 'override-first':dict(exports=1,empty=16,keys=[0,1,2,0,3,4]),
 'override-last':dict(exports=32,empty=2,keys=[0,1,2,3,4,0]),
 'override-pairs':dict(exports=18,empty=0,keys=[0,0,1,1,2,2]),
 'override-cycle':dict(exports=9,empty=0,keys=[0,1,2,0,1,2]),
 'quoted-empty-layout':dict(exports=36,empty=10,keys=[0,1,2,3,4,5]),
 'double-empty':dict(exports=3,empty=48,keys=[0,1,2,3,4,5]),
 'mixed-reference':dict(exports=42,empty=0,keys=[0,1,2,3,4,5]),
 'mixed-override':dict(exports=20,empty=1,keys=[0,1,0,2,1,3]),
}
VALUES=[
 '3000','true','false','null','@N@','-1.25e+3',
 '"@W@#data#kept"', '"A @W@ title # not a comment"',
 'a spaced @W@ value',
 '"Opening @W@ line\n# original text\nSETTING=@N@ remains data\nClosing original line"',
 "'A @W@ message,\npreserve ${USER} and # characters\nin these source lines.'",
 '`Original @W@ body\nCOUNT=@N@ and # raw data\nlast line`',
 '"line\\nnext for @W@"','"${HOST}:$PORT/@W@"',"'./@W@/path # literal'"
]
WORDS='amber birch coral dune ember fennel grove hazel iris jade kestrel linen maple nettle olive pebble quill river sorrel tundra'.split()
def main():
 root=PackSpec.open('dotenv').dataset_root/'sources/curriculum-mixed-v1';files={}
 from packs.dotenv.labeling.label import label
 for index,(family,layout)in enumerate(LAYOUTS.items()):
  for variant in range(24):
   word=WORDS[(index+variant)%len(WORDS)];number=str(random.Random(11111+index*101+variant).randrange(3,90));lines=['# Mixed '+word+' configuration']
   for at,key_index in enumerate(layout['keys']):
    name=word.upper()+'_'+['NAME','PORT','VALUE','OPTION','TEXT','CACHE'][key_index]
    value=''if layout['empty']&(1<<at)else VALUES[(variant+at+index)%len(VALUES)].replace('@W@',word).replace('@N@',number)
    prefix='export 'if layout['exports']&(1<<at)else ''
    lines.append(prefix+name+(' = 'if variant%3==1 else '=')+value+(' # inline note'if variant%2==0 else ''))
   source='\n'.join(lines)+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   if variant%13==3:source='\ufeff'+source
   label(source=source)
   raw=source.encode();p=root/family/f'{variant:02}.env';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve previous dotenv mixed task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original dotenv mixed tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve original dotenv license')
 p.write_bytes(license);lock=dict(format='nsh-dotenv-mixed-v1',generatorSha256=file_hash(Path(__file__)),families=len(LAYOUTS),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve original dotenv mixed lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'mixed files in',len(LAYOUTS),'families')
if __name__=='__main__':main()
