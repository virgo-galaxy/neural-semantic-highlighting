"""Pinned, isolated offline lexer assets. Never imported by neural runtimes.

Extract a pure-Python wheel into ignored artifacts; no pip installation, language
interpreter, database service or system environment modification is involved.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from training.shared.spec import REPOSITORY, file_hash

VERSION='2.21.0'
URL='https://files.pythonhosted.org/packages/71/46/17f022dd3e953bf20a04a028a21ec746d942f8d2af30fa0f124fa0e6a684/pygments-2.21.0-py3-none-any.whl'
SHA256='2363c69b61c4a97c838da3b130dcd6468f4848992b21a82f2a63ec34377137d9'
DIRECTORY=REPOSITORY/'artifacts/tools'/f'pygments-{VERSION}'

def fetch():
    archive=REPOSITORY/'artifacts/cache/gold-tools'/URL.rsplit('/',1)[-1]
    archive.parent.mkdir(parents=True,exist_ok=True)
    if not archive.exists():
        raw=subprocess.check_output(['curl','--fail','--silent','--show-error','--location',URL])
        if hashlib.sha256(raw).hexdigest()!=SHA256:raise ValueError('Offline tool archive hash mismatch')
        archive.write_bytes(raw)
    if file_hash(archive)!=SHA256:raise ValueError('Cached offline tool archive differs')
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    hashes={}
    with zipfile.ZipFile(archive) as wheel:
        for entry in wheel.infolist():
            if entry.is_dir():continue
            path=DIRECTORY/entry.filename
            if not path.resolve().is_relative_to(DIRECTORY.resolve()):raise ValueError('Unsafe offline tool path')
            raw=wheel.read(entry)
            if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve modified offline tool; use a separate tool revision')
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            hashes[entry.filename]=hashlib.sha256(raw).hexdigest()
    lock={'name':'Pygments','version':VERSION,'url':URL,'sha256':SHA256,'files':hashes}
    (DIRECTORY/'source.lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    return lock

def provenance():
    lock=json.loads((DIRECTORY/'source.lock.json').read_text())
    if lock.get('sha256')!=SHA256 or lock.get('version')!=VERSION or not lock.get('files'):raise ValueError('Offline lexer lock missing; run python -m training.shared.offline_tools')
    for name,expected in lock['files'].items():
        if not (DIRECTORY/name).resolve().is_relative_to(DIRECTORY.resolve()) or file_hash(DIRECTORY/name)!=expected:raise ValueError('Offline lexer contents differ')
    return {'name':lock['name'],'version':VERSION,'archiveSha256':SHA256,'files':lock['files']}

def load_lexer(alias):
    # Call provenance once when opening a teacher, not once per source document.
    if str(DIRECTORY) not in sys.path:sys.path.insert(0,str(DIRECTORY))
    import pygments
    from pygments.lexers import get_lexer_by_name
    if pygments.__version__!=VERSION:raise ValueError('Wrong offline lexer version')
    return get_lexer_by_name(alias,stripnl=False,stripall=False,ensurenl=False)

if __name__=='__main__':
    lock=fetch();print('Offline lexer assets:',DIRECTORY,lock['sha256'])
