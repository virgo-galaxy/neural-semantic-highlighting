"""Persistent official parse-only helper. No imports, macros or source execution."""
import atexit
import base64
from dataclasses import dataclass, field
import json
import subprocess
import threading
from .tools import executable, provenance

@dataclass
class Node:
    kind: str
    start: int
    end: int
    token_kind: str = ''
    is_type: bool = False
    field_name: str = ''
    children: list = field(default_factory=list)
    fields: dict = field(default_factory=dict)
    parent: object = None
    raw: bytes = b''

    @property
    def text(self): return self.raw[self.start:self.end].decode('utf-8')
    def descendants(self):
        yield self
        for child in self.children: yield from child.descendants()

_process = None
_lock = threading.Lock()

def close():
    global _process
    if _process is not None:
        _process.stdin.close()
        try: _process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _process.terminate(); _process.wait(timeout=5)
        _process = None
atexit.register(close)

def parse(source):
    global _process
    with _lock:
        if _process is None:
            _process = subprocess.Popen([str(executable())], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        text=True, bufsize=1)
        if _process.poll() is not None: raise ValueError('Offline Swift parser exited unexpectedly')
        raw = source.encode('utf-8')
        _process.stdin.write(base64.b64encode(raw).decode('ascii') + '\n'); _process.stdin.flush()
        line = _process.stdout.readline()
    if not line: raise ValueError('Offline Swift parser returned no result')
    result = json.loads(line)
    if 'error' in result: raise ValueError('SwiftParser rejected source: ' + result['error'])
    def extract(value, parent=None):
        node = Node(value['kind'], value['start'], value['end'], value.get('tokenKind',''),
                    value.get('isType',False), value.get('field',''), parent=parent, raw=raw)
        for child in value.get('children',[]):
            part = extract(child, node); node.children.append(part)
            if part.field_name: node.fields[part.field_name] = part
        return node
    return extract(result['tree']), result['comments']
