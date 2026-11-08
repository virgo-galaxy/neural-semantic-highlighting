"""Short source-position variants of the existing intact grammar families."""
from pathlib import Path
import hashlib
import json
import re
from packs.bash.dataset.generate_curriculum import SH,CSH
from training.shared.spec import PackSpec,file_hash

NAMES={'name':['name','title','owner','subject'],'path':['path','root','location','folder'],
       'entry':['entry','row','file','part'],'item':['item','record','node','value'],
       'count':['count','total','size','level'],'next':['next','updated','remaining','amount'],
       'result':['result','output','answer','data'],'message':['message','greeting','text','notice'],
       'label':['label','caption','tag','description'],'index':['index','step','cursor','offset']}

def main():
    root=PackSpec.open('bash').dataset_root/'sources/fragments-v1';files={}
    for number,profile in enumerate(['posix','bash','zsh','csh']):
        for family,template in (CSH if profile=='csh' else SH).items():
            if profile=='posix':template=template.replace('local item=','item=')
            for index in range(16):
                body=template.format(n=3+index+number*20)
                body=re.sub(r'\b('+'|'.join(NAMES)+r')\b',lambda match:NAMES[match[0]][index%4],body)
                body=body.replace('ready',profile+'-ready').replace('alpha',profile+'-alpha').replace('price',profile+' price').replace(':-default',':-'+profile+'-default')
                body=body.replace('# 原始注释',f'# {profile} 原始注释')
                if index%3==1:body='\n'+body
                elif index%3==2:body='# Short source example\n'+body
                if index%5==1:body=body.replace('\n','\r\n')
                files[f'{profile}/{family}/{index:02}.sh']=body.encode()
    files['LICENSE']=b'Original private neural-semantic-highlighting grammar fragments. No additional license grant.\n'
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve original fragment revision')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-shell-original-fragments-v1','generatorHash':file_hash(Path(__file__)),
          'templateGeneratorHash':file_hash(Path(__file__).with_name('generate_curriculum.py')),
          'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Existing fragment lock differs')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'source fragments')

if __name__=='__main__':main()
