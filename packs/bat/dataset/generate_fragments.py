"""Short-label variants retain their existing related task-family assignments."""
from pathlib import Path
import hashlib,json
from packs.bat.dataset.generate_curriculum import TASKS
from training.shared.spec import PackSpec,file_hash
NAMES=['load','emit','scan','fail','done','run','print','stop','compile_files','check_result','render_line','select_task']
def main():
 root=PackSpec.open('bat').dataset_root/'sources/fragments-v1';files={}
 families=[x for x in TASKS if x.startswith('label-')]
 for family in families:
  for i in range(72):
   source=TASKS[family].format(n=i+13,label=NAMES[i%len(NAMES)])
   if (i//12)%3!=0:source=source.removeprefix('@echo off\n')
   prefix=['','rem Label task\n','\n',':: Label task\n'][(i//18)%4];source=prefix+source
   if i%4==2:source=source.replace('\n','\r\n')
   if i%5==1:source=source.upper()
   files[f'{family}/{i:02}.cmd']=source.encode()
 files['LICENSE']=b'Original private neural-semantic-highlighting BAT label fragments. No additional license grant.\n'
 for name,raw in files.items():
  p=root/name
  if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve existing source')
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 lock={'format':'nsh-bat-label-fragments-v1','generatorHash':file_hash(Path(__file__)),'files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()}}
 p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve source lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'label-name/position tasks')
if __name__=='__main__':main()
