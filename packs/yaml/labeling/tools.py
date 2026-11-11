"""Pinned project-local YAML parser assets; no SDK or global npm install."""
from functools import lru_cache
from pathlib import Path
import base64,hashlib,json,subprocess,tarfile
from training.shared.spec import REPOSITORY,file_hash
CONFIG=Path(__file__).with_name('tools.json')
DIRECTORY=REPOSITORY/'artifacts/tools/yaml-gold/yaml-2.9.1'
LIBRARY=DIRECTORY/'dist/index.js'
def fetch():
 c=json.loads(CONFIG.read_text());archive=REPOSITORY/'artifacts/cache/gold-tools/yaml-2.9.1.tgz';archive.parent.mkdir(parents=True,exist_ok=True)
 if not archive.exists():archive.write_bytes(subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--http1.1','--retry','3','--retry-all-errors','--connect-timeout','15','--max-time','90',c['url']]))
 raw=archive.read_bytes()
 if file_hash(archive)!=c['archiveSha256'] or 'sha512-'+base64.b64encode(hashlib.sha512(raw).digest()).decode()!=c['integrity']:raise ValueError('JSON parser archive integrity mismatch')
 with tarfile.open(archive) as t:
  for item in c['files']:
   member=t.getmember('package/'+item['path'])
   if not member.isfile():raise ValueError('Expected pinned parser file')
   data=t.extractfile(member).read();target=DIRECTORY/item['path']
   if not target.resolve().is_relative_to(DIRECTORY.resolve()) or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Unsafe or changed parser source')
   if target.exists() and target.read_bytes()!=data:raise ValueError('Preserve modified parser cache')
   target.parent.mkdir(parents=True,exist_ok=True)
   if not target.exists():target.write_bytes(data)
 print('Prepared pinned yaml',c['version'])
@lru_cache(maxsize=1)
def provenance():
 c=json.loads(CONFIG.read_text());files={x['path']:x['sha256'] for x in c['files']}
 if any(not (DIRECTORY/name).is_file() or file_hash(DIRECTORY/name)!=h for name,h in files.items()):raise ValueError('Prepare/verify tools with make dataset-yaml-tools')
 node=Path(subprocess.check_output(['which','node'],text=True).strip()).resolve()
 return dict(name=c['name'],version=c['version'],repository=c['repository'],archiveIntegrity=c['integrity'],archiveSha256=c['archiveSha256'],toolConfigHash=file_hash(CONFIG),files=files,license='LICENSE',nodeVersion=subprocess.check_output(['node','--version'],text=True).strip(),nodeSha256=file_hash(node),labelerSha256=file_hash(Path(__file__).with_name('label.mjs')),sourceExecution=False,globalInstall=False)
if __name__=='__main__':fetch();print(json.dumps(provenance(),indent=2))
