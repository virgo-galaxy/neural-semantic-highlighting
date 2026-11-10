"""Pinned project-local Dart parse-only tool; no SDK, pip/npm or global install."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from functools import lru_cache

from training.shared.spec import REPOSITORY, file_hash

CONFIG = Path(__file__).with_name('tools.json')
DIRECTORY = REPOSITORY / 'artifacts/tools/dart-gold/tree-sitter-0.25.10-dart-0.3.0-cc75f92'
LIBRARY = DIRECTORY / ('parser.dylib' if sys.platform == 'darwin' else 'parser.so')


def fetch():
    config = json.loads(CONFIG.read_text())
    sources = {}
    for tool in config['tools']:
        archive = REPOSITORY / 'artifacts/cache/gold-tools' / (tool['id'] + '-' + tool['revision'] + '.tar.gz')
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            raw = subprocess.check_output(['curl', '--fail', '--silent', '--show-error', '--location', '--http1.1',
                '--retry', '3', '--retry-all-errors', f"https://codeload.github.com/{tool['repository']}/tar.gz/{tool['revision']}"])
            archive.write_bytes(raw)
        with tarfile.open(archive) as bundle:
            prefix = bundle.getmembers()[0].name.split('/')[0] + '/'
            for item in tool['files']:
                member = bundle.getmember(prefix + item['path'])
                if not member.isfile(): raise ValueError('Expected original parser source')
                raw = bundle.extractfile(member).read()
                blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
                if blob != item['gitBlob']: raise ValueError('Pinned parser source changed')
                target = DIRECTORY / tool['id'] / item['path']
                if not target.resolve().is_relative_to(DIRECTORY.resolve()): raise ValueError('Unsafe tool source path')
                if target.exists() and target.read_bytes() != raw: raise ValueError('Preserve modified tool sources')
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists(): target.write_bytes(raw)
                sources[str(target.relative_to(DIRECTORY))] = hashlib.sha256(raw).hexdigest()
    runtime, grammar = DIRECTORY / 'tree-sitter/lib', DIRECTORY / 'tree-sitter-dart/src'
    compiler_path = "/Library/Developer/CommandLineTools/usr/bin/clang" if sys.platform == "darwin" and Path("/Library/Developer/CommandLineTools/usr/bin/clang").exists() else "clang"
    compiler = subprocess.check_output([compiler_path, '--version'], text=True).strip()
    command = [compiler_path, '-std=c11', '-O1', '-fPIC', '-dynamiclib' if sys.platform == 'darwin' else '-shared',
               '-I' + str(runtime / 'include'), '-I' + str(grammar), '-I' + str(runtime / 'src'),
               str(runtime / 'src/lib.c'), str(grammar / 'parser.c'), str(grammar / 'scanner.c'), '-o', str(LIBRARY)]
    if sys.platform == 'darwin' and compiler_path.startswith('/Library/Developer/CommandLineTools/'):
        command[1:1] = ['-isysroot', '/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk']
    lock_path = DIRECTORY / 'source.lock.json'
    if LIBRARY.exists():
        if not lock_path.exists(): raise ValueError('Untracked parser binary exists; preserve it and select a new tool directory')
        prior = json.loads(lock_path.read_text())
        if prior['sources'] != sources or prior['compiler'] != compiler or prior['configSha256'] != file_hash(CONFIG):
            raise ValueError('Preserve previous parser build; use a new tool revision')
        if file_hash(LIBRARY) != prior['librarySha256']: raise ValueError('Parser binary differs from its lock')
    else:
        print('Building the offline Dart parser with existing Clang; no SDK installation', flush=True)
        subprocess.run(command, check=True)
        lock = {'format': 'nsh-dart-gold-build-v1', 'configSha256': file_hash(CONFIG),
                'sources': sources, 'compiler': compiler, 'command': command,
                'librarySha256': file_hash(LIBRARY)}
        lock_path.write_text(json.dumps(lock, indent=2) + '\n')
    print('Offline Dart parser:', LIBRARY)


@lru_cache(maxsize=1)
def provenance():
    lock_path = DIRECTORY / 'source.lock.json'
    if not lock_path.exists(): raise ValueError('Run make dataset-dart-tools to build the isolated offline parser')
    lock = json.loads(lock_path.read_text())
    if lock['configSha256'] != file_hash(CONFIG) or file_hash(LIBRARY) != lock['librarySha256']:
        raise ValueError('Offline Dart parser build identity differs')
    for name, expected in lock['sources'].items():
        if file_hash(DIRECTORY / name) != expected: raise ValueError('Pinned parser source differs')
    return {'name': 'Tree-sitter Dart source-local teacher', 'runtimeVersion': '0.25.10', 'grammarVersion': '0.3.0',
            'configSha256': lock['configSha256'], 'sources': lock['sources'],
            'compiler': lock['compiler'], 'librarySha256': lock['librarySha256'], 'sdkRequired': False}


if __name__ == '__main__': fetch()
