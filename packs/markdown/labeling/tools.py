"""Fingerprint existing parse-only Prettier Markdown assets; no download/install."""
from functools import lru_cache
from pathlib import Path
import json,subprocess
from training.shared.spec import REPOSITORY,file_hash
@lru_cache(maxsize=1)
def provenance():
 root=(REPOSITORY/'node_modules/prettier').resolve();entity=(REPOSITORY/'node_modules/entities').resolve();files={}
 for prefix,directory in [('prettier',root),('entities',entity)]:
  for path in sorted(directory.rglob('*')):
   if path.is_file()and(path.suffix in {'.js','.mjs','.cjs','.json'}or path.name.upper().startswith(('LICENSE','LICENCE'))):files[prefix+'/'+str(path.relative_to(directory))]=file_hash(path)
 lock=json.loads(Path(__file__).with_name('tools.json').read_text())
 if files!=lock['files']or json.loads((root/'package.json').read_text())['version']!=lock['version']:raise ValueError('Existing Markdown parser assets changed')
 node=Path(subprocess.check_output(['which','node'],text=True).strip()).resolve()
 return dict(name='Existing Prettier Markdown parser (remark/GFM) and entities',version=lock['version'],entityVersion=json.loads((entity/'package.json').read_text())['version'],reference='https://github.com/prettier/prettier',files=files,toolConfigHash=file_hash(Path(__file__).with_name('tools.json')),nodeVersion=subprocess.check_output(['node','--version'],text=True).strip(),nodeSha256=file_hash(node),labelerSha256=file_hash(Path(__file__).with_name('label.mjs')),parseOnly=True,sourceExecution=False,formatting=False,newSDKInstalled=False,newPackageInstalled=False)
def fetch():
 print('Using existing pinned Prettier Markdown parser; parse only, no install')
 p=provenance();print(p['name'],p['version'],len(p['files']),'verified files')
if __name__=='__main__':fetch()
