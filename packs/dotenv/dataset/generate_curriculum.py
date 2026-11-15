"""Original dotenv assignment-layout families; lexical value forms stay grouped."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
LAYOUTS={'plain':dict(exports=0,empty=0,keys=[0,1,2,3])}
for mask in range(1,16):LAYOUTS[f'exports-{mask:02}']=dict(exports=mask,empty=0,keys=[0,1,2,3])
for mask in range(1,16):LAYOUTS[f'empty-{mask:02}']=dict(exports=0,empty=mask,keys=[0,1,2,3])
for index,keys in enumerate([[0,0,1,2],[0,1,1,2],[0,1,2,2],[0,1,0,2],[0,1,2,0],[0,1,2,1],[0,1,0,1],[0,0,1,1],[0,0,0,0]]):LAYOUTS[f'overrides-{index:02}']=dict(exports=0,empty=0,keys=keys)
VALUES=[
 '@W@-preview','@N@','true','https://@W@.example.test:8080/api?count=@N@',
 '"A @W@ value with # data and \\"quotes\\""',"'C:\\projects\\@W@\\notes $HOME'",
 '"First @W@ line\n# literal data\nKEY=@N@\nlast line"',
 '`Original @W@ data\n${HOME} and # markers\nline @N@`',
 "'{\"name\":\"@W@\",\"count\":@N@,\"ready\":true}'",'${CACHE_DIR:-./@W@}',
 '"escaped newline\\n for @W@ and carriage\\r"',"'first @W@ line\nvalue=@N@\n# literal\nlast'"
]
WORDS='aspen brook cypress delta elm forest glade heath island juniper kelp lotus mist north ocean pine quartz reed sage thyme'.split()
def main():
 root=PackSpec.open('dotenv').dataset_root/'sources/curriculum-v1';files={}
 from packs.dotenv.labeling.label import label
 for index,(family,layout)in enumerate(LAYOUTS.items()):
  for variant in range(24):
   word=WORDS[(index+variant)%len(WORDS)];number=str(random.Random(10101+index*101+variant).randrange(3,90));lines=['# Original '+word+' environment profile']
   for at,key_index in enumerate(layout['keys']):
    name=word.upper()+'_'+['NAME','PORT','VALUE','OPTION'][key_index]
    value=''if layout['empty']&(1<<at)else VALUES[(variant+at*3+index)%len(VALUES)].replace('@W@',word).replace('@N@',number)
    prefix='export 'if layout['exports']&(1<<at)else ''
    text=prefix+name+(' = 'if variant%3==1 else '=')+value
    if variant%4==2:text+=' # source note'
    lines.append(text)
    if variant%7==3:lines.append('# keep a separate comment')
   source='\n'.join(lines)+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   if variant%13==3:source='\ufeff'+source
   label(source=source)
   raw=source.encode();p=root/family/f'{variant:02}.env';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve previous dotenv task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original dotenv tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve original dotenv license')
 p.write_bytes(license);lock=dict(format='nsh-dotenv-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(LAYOUTS),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve original dotenv lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'files in',len(LAYOUTS),'families')
if __name__=='__main__':main()
