"""Original loop-entry fragments, kept with their parent task's frozen family."""
from pathlib import Path
import hashlib
import json
import re
from packs.bash.dataset.generate_programs import SH,CSH
from training.shared.spec import PackSpec,file_hash

def main():
    root=PackSpec.open('bash').dataset_root/'sources/program-fragments-v1';files={}
    for number,profile in enumerate(['posix','bash','zsh','csh']):
        for family,template in (CSH if profile=='csh' else SH).items():
            for index in range(12):
                full=template.format(n=7+index+number*30,fn=['emit','prepare','show','describe'][index%4])
                match=re.search(r'^(?:for|foreach|while)\b',full,re.M)
                if not match:raise ValueError('Task has no top-level loop')
                source=full[match.start():]
                if profile in {'bash','zsh'} and index%2:source=source.replace('if [ ','if [[ ').replace(' ]; then',' ]]; then')
                if index%3==1:source='\n'+source
                elif index%3==2:source=f'# Original {profile} loop fragment\n'+source
                if index%5==1:source=source.replace('\n','\r\n')
                files[f'{profile}/{family}/{index:02}.sh']=source.encode()
    files['LICENSE']=b'Original private neural-semantic-highlighting loop-entry fragments. No additional license grant.\n'
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve previous loop fragment revision')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-shell-original-program-fragments-v1','generatorHash':file_hash(Path(__file__)),
          'parentGeneratorHash':file_hash(Path(__file__).with_name('generate_programs.py')),
          'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Existing fragment lock differs')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'source fragments')

if __name__=='__main__':main()
