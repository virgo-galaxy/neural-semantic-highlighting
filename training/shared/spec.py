"""Pack-owned paths/configuration; importing this module does not load any parser."""
from __future__ import annotations
from dataclasses import dataclass
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import os
from pathlib import Path
import re

REPOSITORY = Path(__file__).resolve().parents[2]
_active = ContextVar('nsh_pack')

def current() -> 'PackSpec':
    """CLI-scoped configuration, isolated across threads and async contexts.

    Runtime objects retain their own manifest/model; this scope is only needed
    while constructing/loading them or running one offline pack command.
    """
    return _active.get()

@contextmanager
def using(pack_id: str):
    handle = _active.set(PackSpec.open(pack_id))
    try: yield current()
    finally: _active.reset(handle)

def file_hash(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""): checksum.update(block)
    return checksum.hexdigest()

def dumps(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(",",":"),allow_nan=False)

@dataclass(frozen=True)
class PackSpec:
    id: str
    label: str
    directory: Path
    document_kinds: tuple[str, ...]
    profiles: tuple[str, ...]
    scope: str

    @classmethod
    def open(cls, pack_id: str):
        if not re.fullmatch(r"[a-z][a-z0-9-]*",pack_id):raise ValueError("Invalid pack identifier")
        root=REPOSITORY/'packs'/pack_id
        manifest=json.loads((root/'manifest.json').read_text())
        config=json.loads((root/'pack.json').read_text())
        kinds=tuple(item['id'] for item in manifest['documentKinds'])
        profiles=tuple(config['profiles'])
        if manifest['id']!=pack_id or not kinds or not profiles or len(set(kinds))!=len(kinds) or len(set(profiles))!=len(profiles):raise ValueError('Invalid pack manifest/profiles')
        return cls(pack_id,config['label'],root,kinds,profiles,config['scope'])

    @property
    def schema_path(self):return self.directory/'schema.json'
    @property
    def semantics_path(self):return self.directory/'SEMANTICS.md'
    @property
    def dataset_root(self):return Path(os.environ.get('NSH_DATASET_ROOT','~/Datasets/neural-semantic-highlighting')).expanduser()/self.id
    @property
    def checkpoint_format(self):return f'nsh-{self.id}-checkpoint-v1'
    @property
    def model_format(self):return f'nsh-{self.id}-model-v1'
    @property
    def dataset_format(self):return f'nsh-{self.id}-byte-dataset-v1'

    def schema(self):
        data=json.loads(self.schema_path.read_text());return {'tokenTypes':[item['id'] for item in data['tokenTypes']], 'modifiers':[item['id'] for item in data['tokenModifiers']]}

def code_hashes(spec: PackSpec):
    files=list(Path(__file__).parent.glob('*.py'))
    files += list((REPOSITORY/'training'/spec.id).rglob('*.py'))
    files += [REPOSITORY/'training/html'/name for name in ('model.py','inference.py','losses.py','io.py')]
    return {str(path.relative_to(REPOSITORY)):file_hash(path) for path in sorted(set(files))}
