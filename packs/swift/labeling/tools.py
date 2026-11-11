"""Build a parse-only helper from the already installed official Swift 6.4.2."""
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import os
import subprocess
from training.shared.spec import REPOSITORY, file_hash, dumps

SOURCE = Path(__file__).with_name('SwiftTree.swift')
VERSION = '6.4.2'
DIRECTORY = REPOSITORY / 'artifacts/tools/swift-gold'

@lru_cache(maxsize=1)
def provenance():
    root = Path(os.environ.get('NSH_SWIFT_TOOLCHAIN', str(Path.home() / 'Library/Developer/Toolchains/swift-6.4.2-RELEASE.xctoolchain'))).expanduser().resolve()
    compiler = root / 'usr/bin/swiftc'
    version = subprocess.check_output([str(compiler), '--version'], text=True).strip()
    if 'Swift version 6.4.2 ' not in version:
        raise ValueError('Gold requires the pinned existing Swift 6.4.2 toolchain')
    host = root / 'usr/lib/swift/host'
    dependencies = [compiler.resolve(), *[host / ('lib' + name + '.dylib') for name in ['SwiftSyntax','SwiftParser','SwiftParserDiagnostics','SwiftDiagnostics']]]
    return {'name': 'Official SwiftParser source-local teacher', 'version': VERSION,
            'toolchain': str(root), 'compiler': version, 'sourceSha256': file_hash(SOURCE),
            'dependencies': {str(p.relative_to(root)): file_hash(p) for p in dependencies},
            'parseOnly': True, 'macroExpansion': False, 'typeChecking': False}

def executable():
    identity = provenance()
    key = hashlib.sha256(dumps(identity).encode()).hexdigest()
    folder = DIRECTORY / key
    binary = folder / 'swift-tree'
    lock = folder / 'build.json'
    if binary.exists():
        prior = json.loads(lock.read_text())
        if prior['identity'] != identity or prior['binarySha256'] != file_hash(binary):
            raise ValueError('Preserve previous Swift parser helper and select a new revision')
        return binary
    folder.mkdir(parents=True, exist_ok=True)
    root = Path(identity['toolchain']); host = root / 'usr/lib/swift/host'
    sdk = '/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk'
    env = dict(os.environ, SWIFT_DRIVER_CLANG_EXEC='/Library/Developer/CommandLineTools/usr/bin/clang')
    command = [str(root / 'usr/bin/swiftc'), '-O', '-sdk', sdk, '-I', str(host), '-L', str(host),
               '-Xlinker', '-rpath', '-Xlinker', str(host), '-lSwiftSyntax', '-lSwiftParser',
               '-lSwiftParserDiagnostics', str(SOURCE), '-o', str(binary)]
    compiled = subprocess.run(command, env=env, capture_output=True, text=True)
    if compiled.returncode: raise ValueError('Offline Swift helper build failed: ' + compiled.stderr)
    lock.write_text(json.dumps({'identity': identity, 'command': command, 'binarySha256': file_hash(binary)}, indent=2) + '\n')
    return binary

if __name__ == '__main__': print(executable())
