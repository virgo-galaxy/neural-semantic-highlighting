"""Offline parse-only JDK teacher. Never imported by a neural runtime."""
from __future__ import annotations

import atexit
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading

from training.shared.spec import REPOSITORY, file_hash

SOURCE = Path(__file__).with_name('JavaGold.java')
EXPORTS = [f'--add-exports=jdk.compiler/com.sun.tools.javac.{package}=ALL-UNNAMED'
           for package in ('parser', 'util')]
_process = None
_identity = None
_lock = threading.Lock()


def jdk_home():
    home = os.environ.get('NSH_JAVA_HOME') or subprocess.check_output(
        ['/usr/libexec/java_home', '-v', '22'], text=True).strip()
    home = Path(home).expanduser().resolve()
    if '22.0.1' not in (home / 'release').read_text():
        raise ValueError('Gold requires the pinned JDK 22.0.1; set NSH_JAVA_HOME explicitly')
    return home


def provenance():
    global _identity
    if _identity is None:
        home = jdk_home()
        _identity = {'name': 'OpenJDK parse-only scanner/tree teacher', 'version': '22.0.1',
                     'releaseSha256': file_hash(home / 'release'),
                     'compilerModuleSha256': file_hash(home / 'jmods/jdk.compiler.jmod'),
                     'teacherSha256': file_hash(SOURCE), 'sourceLevel': 22,
                     'annotationProcessing': False, 'semanticAnalysis': False}
    return dict(_identity)


def close():
    global _process
    if _process is not None:
        _process.stdin.close()
        try:
            _process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _process.terminate()
            _process.wait(timeout=5)
        _process = None


atexit.register(close)


def _open():
    global _process
    if _process is not None:
        if _process.poll() is not None:
            raise ValueError('Offline JDK teacher exited unexpectedly')
        return _process
    home = jdk_home()
    key = hashlib.sha256(json.dumps(provenance(), sort_keys=True).encode()).hexdigest()
    output = REPOSITORY / 'artifacts/tools/java-gold' / key
    output.mkdir(parents=True, exist_ok=True)
    if not (output / 'JavaGold.class').exists():
        compiled = subprocess.run([str(home / 'bin/javac'), *EXPORTS, '-d', str(output), str(SOURCE)],
                                  capture_output=True, text=True)
        if compiled.returncode:
            raise ValueError('Offline teacher compilation failed: ' + compiled.stderr)
    _process = subprocess.Popen([str(home / 'bin/java'), *EXPORTS, '-Xmx512m', '-cp', str(output), 'JavaGold'],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    return _process


def label(*, source: str, document_kind='java', profile='java') -> dict:
    if document_kind != 'java' or profile != 'java' or '\0' in source:
        raise ValueError('Expected original Java source')
    raw = source.encode('utf-8')
    with _lock:
        process = _open()
        process.stdin.write(base64.b64encode(raw).decode('ascii') + '\n')
        process.stdin.flush()
        response = process.stdout.readline().rstrip('\n')
    if not response.startswith('OK\t'):
        message = base64.b64decode(response.split('\t', 1)[1]).decode() if response.startswith('ERROR\t') else response
        raise ValueError('JDK rejected source: ' + message)
    result = json.loads(response[3:])
    return {'documentKind': 'java', 'offsetEncoding': 'utf-16', **result}
