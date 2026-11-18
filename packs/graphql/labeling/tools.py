"""Pinned parse-only GraphQL source, project-local and never imported by inference."""
from pathlib import Path
from functools import lru_cache
import hashlib,io,json,subprocess,sys,zipfile
from training.shared.spec import REPOSITORY,file_hash
CONFIG=Path(__file__).with_name('tools.json')
DIRECTORY=REPOSITORY/'artifacts/tools/graphql-core-3.3.2'
def fetch():
 config=json.loads(CONFIG.read_text());DIRECTORY.mkdir(parents=True,exist_ok=True)
 raw=subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--http1.1',config['url']])
 if hashlib.sha256(raw).hexdigest()!=config['sha256']:raise ValueError('GraphQL tool archive changed')
 with zipfile.ZipFile(io.BytesIO(raw))as bundle:
  for name in bundle.namelist():
   if name.endswith('/'):continue
   path=DIRECTORY/name
   if not path.resolve().is_relative_to(DIRECTORY.resolve()):raise ValueError('Unsafe tool member')
   content=bundle.read(name)
   if path.exists()and path.read_bytes()!=content:raise ValueError('Preserve previous parser source')
   path.parent.mkdir(parents=True,exist_ok=True)
   if not path.exists():path.write_bytes(content)
 lock=dict(url=config['url'],sha256=config['sha256'],files={str(p.relative_to(DIRECTORY)):file_hash(p)for p in DIRECTORY.rglob('*')if p.is_file()and p.name!='source.lock.json'and '__pycache__'not in p.parts})
 target=DIRECTORY/'source.lock.json'
 if target.exists()and json.loads(target.read_text())!=lock:raise ValueError('Preserve parser lock')
 target.write_text(json.dumps(lock,indent=2)+'\n');print('GraphQL offline parser ready; no installation')
@lru_cache(maxsize=1)
def provenance():
 lock=json.loads((DIRECTORY/'source.lock.json').read_text());config=json.loads(CONFIG.read_text())
 if lock['sha256']!=config['sha256']:raise ValueError('Tool lock differs from config')
 for name,sha in lock['files'].items():
  if file_hash(DIRECTORY/name)!=sha:raise ValueError('Offline parser source changed')
 sys.path.insert(0,str(DIRECTORY))
 import graphql
 if graphql.__version__!=config['version']:raise ValueError('Unexpected GraphQL parser version')
 return dict(name=config['name'],version=config['version'],configSha256=file_hash(CONFIG),sourceLockSha256=file_hash(DIRECTORY/'source.lock.json'),labelerSha256=file_hash(Path(__file__).with_name('label.py')),sourceExecution=False,globalInstall=False,newSDKInstalled=False)
if __name__=='__main__':fetch()
