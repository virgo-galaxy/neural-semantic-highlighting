"""Verify pinned project-local npm assets. No SDK or global npm installation."""
from functools import lru_cache
from pathlib import Path
import base64,hashlib,json,subprocess,tarfile
from training.shared.spec import REPOSITORY,file_hash
CONFIG=Path(__file__).with_name('tools.json')
DIRECTORY=REPOSITORY/'artifacts/tools/toml-gold/node_modules'
LIBRARY=DIRECTORY/'toml-eslint-parser/lib/index.mjs'
def fetch():
 c=json.loads(CONFIG.read_text())
 for package in c['packages']:
  archive=REPOSITORY/'artifacts/cache/gold-tools'/f"{package['name']}-{package['version']}.tgz";archive.parent.mkdir(parents=True,exist_ok=True)
  if not archive.exists():archive.write_bytes(subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--retry','3',package['url']]))
  raw=archive.read_bytes()
  if file_hash(archive)!=package['archiveSha256'] or 'sha512-'+base64.b64encode(hashlib.sha512(raw).digest()).decode()!=package['integrity']:raise ValueError('TOML tool integrity mismatch')
  folder=DIRECTORY/package['name']
  with tarfile.open(archive) as t:
   for item in package['files']:
    member=t.getmember('package/'+item['path']);target=folder/item['path']
    if not member.isfile() or not target.resolve().is_relative_to(folder.resolve()):raise ValueError('Unsafe pinned tool file')
    data=t.extractfile(member).read()
    if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Changed tool file')
    if target.exists() and target.read_bytes()!=data:raise ValueError('Preserve modified tool cache')
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():target.write_bytes(data)
 print('Prepared pinned TOML tools')
@lru_cache(maxsize=1)
def provenance():
 c=json.loads(CONFIG.read_text())
 for package in c['packages']:
  for item in package['files']:
   p=DIRECTORY/package['name']/item['path']
   if not p.is_file() or file_hash(p)!=item['sha256']:raise ValueError('Prepare/verify tools with make dataset-toml-tools')
 node=Path(subprocess.check_output(['which','node'],text=True).strip()).resolve()
 return dict(repository=c['repository'],packages=c['packages'],toolConfigHash=file_hash(CONFIG),nodeVersion=subprocess.check_output(['node','--version'],text=True).strip(),nodeSha256=file_hash(node),labelerSha256=file_hash(Path(__file__).with_name('label.mjs')),sourceExecution=False,globalInstall=False)
if __name__=='__main__':fetch();print(json.dumps(provenance(),indent=2))
