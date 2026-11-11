"""Persistent official Kotlin PSI/lexer; original UTF-16 offsets, no source execution."""
import atexit,base64,json,subprocess,threading
from dataclasses import dataclass,field
from .tools import executable,provenance

@dataclass
class Node:
    kind:str
    start:int
    end:int
    field_name:str=''
    syntax_type:str=''
    meta:dict=field(default_factory=dict)
    children:list=field(default_factory=list)
    fields:dict=field(default_factory=dict)
    parent:object=None
    raw:bytes=b''
    @property
    def text(self):return self.raw[self.start*2:self.end*2].decode('utf-16-le')
    def descendants(self):
        yield self
        for c in self.children:yield from c.descendants()

_process=None
_lock=threading.Lock()
def close():
    global _process
    if _process is not None:
        _process.stdin.close()
        try:_process.wait(timeout=5)
        except subprocess.TimeoutExpired:_process.terminate();_process.wait(timeout=5)
        _process=None
atexit.register(close)

def parse(source,script=False):
    global _process
    with _lock:
        if _process is None:_process=subprocess.Popen(executable(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
        if _process.poll() is not None:raise ValueError('Official Kotlin parser process exited')
        _process.stdin.write(('script' if script else 'code')+'\t'+base64.b64encode(source.encode('utf-8')).decode()+'\n');_process.stdin.flush()
        response=_process.stdout.readline()
    if not response:raise ValueError('Official Kotlin parser returned no response')
    result=json.loads(response)
    if 'error' in result:raise ValueError('Official Kotlin parser rejected source: '+result['error'])
    raw=source.encode('utf-16-le')
    def extract(value,parent=None):
        n=Node(value['kind'],value['start'],value['end'],value.get('field',''),value.get('syntaxType',''),value,parent=parent,raw=raw)
        for item in value.get('children',[]):
            c=extract(item,n);n.children.append(c)
            if c.field_name:n.fields[c.field_name]=c
        return n
    return extract(result['tree']),result['tokens']
