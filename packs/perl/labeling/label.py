"""Offline PPI Gold, reading original source without compiling/executing it."""
from __future__ import annotations
import atexit
from functools import lru_cache
import json
from pathlib import Path
import re
import subprocess
import threading
from training.shared.spec import file_hash

KEYWORDS=set('use no require package sub my our local state if elsif else unless while until for foreach continue given when default do return last next redo goto eval BEGIN UNITCHECK CHECK INIT END __SUB__ __FILE__ __LINE__ class method field ADJUST async await'.split())
WORD_OPERATORS=set('and or xor not eq ne lt gt le ge cmp x isa'.split())
IDENTIFIER=re.compile(r'[^\W\d]\w*\Z',re.UNICODE)

class Parser:
    def __init__(self):
        self.process=subprocess.Popen(['/usr/bin/perl',str(Path(__file__).with_name('ppi.pl'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,encoding='utf-8',bufsize=1)
        self.lock=threading.Lock();atexit.register(self.close)
    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            try:self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:self.process.terminate()
    def parse(self,source):
        with self.lock:
            self.process.stdin.write(json.dumps({'source':source},ensure_ascii=True)+'\n');self.process.stdin.flush()
            line=self.process.stdout.readline()
            if not line:raise ValueError('Offline PPI worker exited')
            result=json.loads(line)
            if result.get('error'):raise ValueError(result['error'])
            if result.get('ppiVersion')!='1.270':raise ValueError('Expected the frozen PPI version')
            return result['tokens']

@lru_cache(maxsize=1)
def parser():return Parser()

def provenance():
    root=Path('/System/Library/Perl/Extras/5.34')
    paths=[root/'PPI.pm',*sorted((root/'PPI').rglob('*.pm'))]
    return {'name':'PPI','version':'1.270','hostPerl':'5.34','binarySha256':file_hash(Path('/usr/bin/perl')),
            'modules':{str(p):file_hash(p) for p in paths}}

def label(*,source,document_kind='perl',profile='perl5'):
    if document_kind!='perl' or profile!='perl5' or '\0' in source:raise ValueError('Expected original Perl 5 source')
    # PPI uses LF internally. The view is offline only; every boundary maps back
    # to original characters, including CRLF, tabs and non-BMP Unicode.
    view='';mapping=[0];i=0
    while i<len(source):
        char=source[i];step=2 if source[i:i+2]=='\r\n' else 1
        view+='\n' if step==2 else char;i+=step;mapping.append(i)
    lines=view.splitlines(keepends=True);line_starts=[0]
    for line in lines:line_starts.append(line_starts[-1]+len(line))
    units=[0]
    for char in source:units.append(units[-1]+(2 if ord(char)>65535 else 1))
    tokens=[];opaque=[];body_cursors={};features={'profile:perl5'}
    for token in parser().parse(view):
        text=token['text'];kind=token['class'].removeprefix('PPI::Token::')
        if not text:continue
        row,column=token['location'][:2];a=line_starts[row-1]+column-1;b=a+len(text)
        if view[a:b]!=text:raise ValueError('PPI token no longer matches original source')
        if kind=='HereDoc':
            newline=view.find('\n',b)
            if newline<0:raise ValueError('Incomplete Here Document')
            start=body_cursors.get(newline,newline+1);line_index=view.count('\n',0,start)
            end_index=line_index+token['bodyLines']
            if end_index>=len(lines):raise ValueError('Missing Here Document terminator')
            terminator=lines[end_index].rstrip('\r\n')
            if (terminator.lstrip(' \t') if text.startswith('<<~') else terminator)!=token['terminator']:raise ValueError('Here Document terminator differs from original source')
            finish=line_starts[end_index]+len(terminator)
            opaque.append((start,finish,'string',[]));body_cursors[newline]=line_starts[end_index+1];features.add('heredocs')
        if kind=='Whitespace':continue
        if kind in {'Comment','Pod','Data','End'}:
            text=text.rstrip();b=a+len(text)
        if text:tokens.append({**token,'kind':kind,'a':a,'b':b,'text':text})
    # Join PPI's split Cast + Unicode bareword for use-utf8 variable spelling.
    joined=[]
    for t in tokens:
        if joined and joined[-1]['kind']=='Cast' and joined[-1]['text'] in {'$','@','%'} and joined[-1]['b']==t['a'] and t['kind']=='Word' and IDENTIFIER.fullmatch(t['text']):
            previous=joined.pop();t={**t,'a':previous['a'],'text':previous['text']+t['text'],'kind':'Symbol'}
        joined.append(t)
    tokens=joined;definitions=set();decl_names=set()
    for index,t in enumerate(tokens):
        previous=tokens[index-1]['text'] if index else None
        if t['kind']=='Word' and previous=='sub':definitions.add(index);decl_names.add(t['text'])
    spans=[]
    for index,t in enumerate(tokens):
        text,kind=t['text'],t['kind'];previous=tokens[index-1]['text'] if index else None;following=tokens[index+1]['text'] if index+1<len(tokens) else None;mods=[]
        if kind in {'Comment','Pod','Data','End'} or text in {'__DATA__','__END__'}:role='comment';features.add('comments')
        elif kind.startswith(('Quote','HereDoc')):
            role='regexp' if kind.startswith('Regexp') or 'Regexp' in kind else 'string';features.add('strings')
            if role=='regexp':features.add('regexps')
        elif kind.startswith('Regexp'):role='regexp';features.add('regexps')
        elif kind.startswith('Number'):role='number'
        elif kind in {'Symbol','Magic','ArrayIndex'}:
            role='variable';features.add('variables')
            if t.get('declaration') or previous in {'my','our','local','state'}:mods=['declaration']
        elif kind in {'Structure','Separator'} or text==',':role='punctuation'
        elif kind=='Operator' or kind=='Cast':role='operator'
        elif kind=='Label':role='label';mods=['declaration']
        elif kind=='Prototype':role='parameter';features.add('prototypes')
        elif kind=='Attribute':role='property'
        elif kind=='Word':
            if index in definitions:role='function';mods=['declaration'];features.add('functions')
            elif previous in {'package','use','no','require'} and text not in KEYWORDS:role='namespace'
            elif t.get('method') or previous=='->':role='method'
            elif following=='=>':role='property'
            elif text in WORD_OPERATORS:role='operator'
            elif text in KEYWORDS:role='keyword'
            elif text in decl_names:role='function'
            elif t.get('builtin'):role='function';mods=['default-library']
            elif following=='(' or '::' in text:role='function'
            elif previous=='{' and following=='}':role='property'
            else:role='string'
        else:raise ValueError('Unsupported PPI token '+kind)
        if role=='keyword':
            if text in {'if','elsif','else','unless'}:features.add('conditionals')
            if text in {'while','until','for','foreach'}:features.add('loops')
        spans.append((t['a'],t['b'],role,mods))
    spans+=opaque;spans.sort();output=[]
    for a,b,role,mods in spans:
        item={'start':units[mapping[a]],'end':units[mapping[b]],'tokenType':role}
        if mods:item['modifiers']=mods
        output.append(item)
    if '\r\n' in source:features.add('crlf')
    if any(ord(char)>127 for char in source):features.add('unicode')
    return {'offsetEncoding':'utf-16','spans':output,'features':sorted(features)}
