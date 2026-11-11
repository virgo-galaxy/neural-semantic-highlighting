"""Original JSON/JSONC supervision via a pinned independent parser; offline only."""
from pathlib import Path
import atexit,json,subprocess,threading
from .tools import LIBRARY,provenance
_process=None
_lock=threading.Lock()
def close():
 global _process
 if _process is not None:
  if _process.stdin:_process.stdin.close()
  try:_process.wait(timeout=5)
  except subprocess.TimeoutExpired:_process.terminate();_process.wait(timeout=5)
  _process=None
atexit.register(close)
def label(*,source,document_kind='json',profile=None):
 global _process
 profile=profile or document_kind
 if document_kind not in {'json','jsonc'} or profile!=document_kind or not isinstance(source,str):raise ValueError('Expected a matching JSON/JSONC kind/profile')
 source.encode('utf-8');provenance()
 with _lock:
  if _process is None or _process.poll() is not None:_process=subprocess.Popen(['node',str(Path(__file__).with_name('label.mjs')),str(LIBRARY)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,encoding='utf-8')
  _process.stdin.write(json.dumps(dict(source=source,documentKind=document_kind),ensure_ascii=True)+'\n');_process.stdin.flush();line=_process.stdout.readline()
  if not line:raise RuntimeError('Offline JSON teacher stopped')
  result=json.loads(line)
  if 'error' in result:raise ValueError(result['error'])
  return result['result']
