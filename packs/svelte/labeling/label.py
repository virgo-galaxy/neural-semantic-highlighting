"""Persistent offline JSONL bridge. Components are parsed, never compiled/run."""
import atexit,json,subprocess
from pathlib import Path
from .tools import provenance

_process=None
def close():
    global _process
    if _process is not None:
        _process.stdin.close();_process.wait(timeout=10);_process=None
atexit.register(close)

def label(*,source,document_kind='svelte',profile='svelte'):
    global _process
    if document_kind!='svelte' or profile!='svelte' or '\0' in source:raise ValueError('Expected original Svelte source')
    provenance()
    if _process is None:_process=subprocess.Popen(['node',str(Path(__file__).with_name('teacher.mjs'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,encoding='utf-8')
    _process.stdin.write(json.dumps(dict(source=source))+'\n');_process.stdin.flush()
    line=_process.stdout.readline()
    if not line:raise ValueError('Svelte teacher terminated')
    result=json.loads(line)
    if 'error' in result:raise ValueError(result['error'])
    return result
