"""Pinned parse-only BuildKit helper, built with existing Go in isolated caches."""
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import os
import subprocess

from training.shared.spec import REPOSITORY, file_hash

ROOT = REPOSITORY / 'artifacts/tools/dockerfile-gold'
HERE = Path(__file__).resolve().parent
CONFIG = HERE / 'tools.json'


def source_hashes():
    return {name: file_hash(HERE / name) for name in ('tools.json', 'parser/main.go', 'parser/go.mod', 'parser/go.sum')}


def directory():
    identity = json.dumps(source_hashes(), sort_keys=True).encode()
    return ROOT / ('buildkit-v0.35.0-' + hashlib.sha256(identity).hexdigest()[:16])


def binary():
    return directory() / 'dockerfile-parser'


def fetch():
    target = directory()
    target.mkdir(parents=True, exist_ok=True)
    lock = target / 'source.lock.json'
    if lock.exists():
        provenance()
        print('Reused verified official BuildKit parse-only helper')
        return
    if binary().exists():
        raise ValueError('Preserve incomplete helper build; choose a new tool revision')
    env = {**os.environ, 'GOTOOLCHAIN': 'local', 'GOPATH': str(ROOT / 'gopath'),
           'GOMODCACHE': str(ROOT / 'modules'), 'GOCACHE': str(ROOT / 'build-cache')}
    subprocess.run(['go', 'build', '-mod=readonly', '-trimpath', '-buildvcs=false', '-o', str(binary()), '.'],
                   cwd=HERE / 'parser', env=env, check=True)
    config = json.loads(CONFIG.read_text())
    module = json.loads(subprocess.check_output(['go', 'mod', 'download', '-json', 'github.com/moby/buildkit@v0.35.0'],
                                               cwd=HERE / 'parser', env=env, text=True))
    if module['Sum'] != config['moduleSum'] or module['GoModSum'] != config['goModSum']:
        raise ValueError('BuildKit module checksum differs from pinned tool configuration')
    go = Path(subprocess.check_output(['which', 'go'], text=True).strip()).resolve()
    record = dict(**config, parserSha256=file_hash(binary()), sources=source_hashes(),
                  goVersion=subprocess.check_output(['go', 'version'], text=True).strip(), goSha256=file_hash(go),
                  modulesSha256=file_hash(HERE / 'parser/go.sum'), sdkDownloadAllowed=False, globalInstall=False)
    lock.write_text(json.dumps(record, indent=2) + '\n')
    print('Prepared official BuildKit v0.35.0 parse-only helper; no Docker Engine or SDK installation')


@lru_cache(maxsize=1)
def provenance():
    lock = directory() / 'source.lock.json'
    if not lock.exists():
        raise ValueError('Prepare offline tools with make dataset-dockerfile-tools')
    record = json.loads(lock.read_text())
    if record['sources'] != source_hashes() or record['parserSha256'] != file_hash(binary()):
        raise ValueError('Dockerfile offline helper changed')
    return record


if __name__ == '__main__':
    fetch()
