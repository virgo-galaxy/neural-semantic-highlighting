"""Pinned official Zig SDK parser build; no external grammar or dependencies."""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import json,subprocess
from training.shared.spec import REPOSITORY,file_hash
CONFIG=Path(__file__).with_name('tools.json')
DIRECTORY=REPOSITORY/'artifacts/tools/zig-gold/0.17.1'
LIBRARY=DIRECTORY/'teacher'

def sdk():
    c=json.loads(CONFIG.read_text());root=Path(c['sdk']);compiler=root/c['compiler']
    if subprocess.check_output([str(compiler),'version'],text=True).strip()!=c['version']:raise ValueError('Zig Gold requires exactly 0.17.1')
    return c,root,compiler

def identity():
    c,root,compiler=sdk();lib=root/c['library'];sources={str(p.relative_to(root)):file_hash(p) for p in sorted((lib/'std').rglob('*.zig'))}
    return dict(format='nsh-zig-gold-tools-lock-v1',version=c['version'],configSha256=file_hash(CONFIG),teacherSha256=file_hash(Path(__file__).with_name('teacher.zig')),compiler=str(compiler),compilerSha256=file_hash(compiler),sdkSources=sources,licenseSha256=file_hash(root/'LICENSE'))

def fetch():
    lock=identity();DIRECTORY.mkdir(parents=True,exist_ok=True);p=DIRECTORY/'source.lock.json'
    if LIBRARY.exists():
        old=json.loads(p.read_text());expected={k:v for k,v in old.items() if k not in ['binarySha256','command']}
        if expected!=lock or file_hash(LIBRARY)!=old['binarySha256']:raise ValueError('Preserve prior Zig Gold build; use a new revision')
    else:
        command=[lock['compiler'],'build-exe',str(Path(__file__).with_name('teacher.zig')),'-O','ReleaseSafe','-lc','-femit-bin='+str(LIBRARY),'--cache-dir',str(REPOSITORY/'artifacts/zig/build-cache'),'--global-cache-dir',str(REPOSITORY/'artifacts/zig/global-cache')]
        subprocess.run(command,check=True);lock.update(binarySha256=file_hash(LIBRARY),command=command);p.write_text(json.dumps(lock,indent=2)+'\n')
    print('Official Zig 0.17.1 offline parser:',LIBRARY)

@lru_cache(maxsize=1)
def provenance():
    c,root,compiler=sdk();lock=json.loads((DIRECTORY/'source.lock.json').read_text())
    if lock['configSha256']!=file_hash(CONFIG) or lock['teacherSha256']!=file_hash(Path(__file__).with_name('teacher.zig')) or lock['compilerSha256']!=file_hash(compiler) or lock['binarySha256']!=file_hash(LIBRARY):raise ValueError('Zig Gold tool identity differs')
    for name,expected in lock['sdkSources'].items():
        if file_hash(root/name)!=expected:raise ValueError('Pinned SDK source changed')
    return dict(name='Official Zig 0.17.1 Ast/Tokenizer and ast-check',**lock,sourceExecution=False,typeChecking=False,importsFollowed=False)
if __name__=='__main__':fetch()
