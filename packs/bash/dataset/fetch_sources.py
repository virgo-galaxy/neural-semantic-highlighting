"""Capture selected upstream shell source/license files without installing shells."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
from training.shared.spec import PackSpec, REPOSITORY

BASH_URL='https://ftp.gnu.org/gnu/bash/bash-5.3.tar.gz'
BASH_SHA='0d5cd86965f869a26cf64f4b71be7b96f90a3ba8b3d74e27e8e9d9d5550f31ba'
ZSH_REV='73d317384c9225e46d66444f93b46f0fbe7084ef'
TCSH_REV='f773aba56aa128a38712987b1b8bdbc393d1e4d0'
ZSH_FILES=['Functions/Misc/'+name for name in ['add-zsh-hook','allopt','checkmail','colors','getjobs','harden','is-at-least','nslookup','promptnl','relative','run-help','run-help-git','run-help-ip','run-help-sudo','sticky-note','zargs','zcalc','zed','zkbd','zmathfuncdef','zmv','zrecompile','ztodo']]
TCSH_FILES=['complete.tcsh','cygwin/bindkey.tcsh','cygwin/csh.cshrc','cygwin/csh.login','debian/csh.cshrc','debian/csh.login','dot.login','dot.tcshrc','win32/example.tcshrc']

def fetch(url):return subprocess.check_output(['curl','--fail','--silent','--show-error','--location',url])

def write_root(root,files,identity):
    root.mkdir(parents=True,exist_ok=True)
    hashes={}
    for name,raw in files.items():
        path=root/name
        if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe source path')
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve existing source revision')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        hashes[name]=hashlib.sha256(raw).hexdigest()
    lock={**identity,'files':hashes};path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Existing source lock differs')
    path.write_text(json.dumps(lock,indent=2)+'\n')

def main():
    spec=PackSpec.open('bash');parent=spec.dataset_root/'sources'
    archive=REPOSITORY/'artifacts/tools/bash-5.3.tar.gz'
    archive.parent.mkdir(parents=True,exist_ok=True)
    if not archive.exists():archive.write_bytes(fetch(BASH_URL))
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=BASH_SHA:raise ValueError('Bash source archive differs')
    files={};profiles={'bash':[],'posix':[]}
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            relative=member.name.removeprefix('bash-5.3/')
            if not member.isfile():continue
            if relative=='COPYING':files[relative]=bundle.extractfile(member).read();continue
            if not 30<member.size<20000 or not relative.startswith(('examples/functions/','examples/scripts/','support/')):continue
            raw=bundle.extractfile(member).read()
            try:source=raw.decode('utf-8')
            except UnicodeError:continue
            if '\0' in source:continue
            first=source.split('\n',1)[0]
            if first.startswith('#!') and ('/sh' in first or 'env sh' in first):profile='posix'
            elif relative.startswith(('examples/functions/','examples/scripts/')) and not relative.endswith(('README','INDEX')):profile='bash'
            else:continue
            files[relative]=raw;profiles[profile].append(relative)
    write_root(parent/'bash-5.3',files,{'url':BASH_URL,'archiveSha256':BASH_SHA,'profiles':profiles})
    for project,revision,names,license_name,folder in [('zsh-users/zsh',ZSH_REV,ZSH_FILES,'LICENCE','zsh-5.9'),('tcsh-org/tcsh',TCSH_REV,TCSH_FILES,'Copyright','tcsh-6.24.16')]:
        all_names=[*names,license_name]
        def download(name):return name,fetch(f'https://raw.githubusercontent.com/{project}/{revision}/{name}')
        with ThreadPoolExecutor(max_workers=6) as pool:captured=dict(pool.map(download,all_names))
        write_root(parent/folder,captured,{'repository':project,'commit':revision,'sourceFiles':names,'licenseFile':license_name})
    print('Captured source only:',parent)

if __name__=='__main__':main()
