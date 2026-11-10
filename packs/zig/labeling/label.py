"""Current Zig 0.17.1 syntax/local bindings; input never compiles or executes."""
from __future__ import annotations
import json,subprocess
from .tools import LIBRARY,provenance

PUNCTUATION={'l_paren','r_paren','l_brace','r_brace','l_bracket','r_bracket','comma','semicolon','colon','period','ellipsis3','ellipsis2','equal_angle_bracket_right'}

def label(*,source,document_kind='zig',profile='zig'):
    if document_kind!='zig' or profile!='zig' or '\0' in source:raise ValueError('Expected original Zig 0.17.1 source')
    tools=provenance();raw=source.encode()
    check=subprocess.run([tools['compiler'],'ast-check','--color','off'],input=raw,capture_output=True)
    if check.returncode:raise ValueError('Current Zig ast-check: '+check.stderr.decode('utf-8').strip())
    run=subprocess.run([str(LIBRARY)],input=raw,capture_output=True)
    if run.returncode:raise ValueError('Official Zig parser rejected source: '+run.stderr.decode('utf-8').strip())
    data=json.loads(run.stdout);tokens=data['tokens'];nodes=data['nodes'];roles={};features=set()
    for t in tokens:t['text']=raw[t['start']:t['end']].decode()
    scopes=[dict(first=0,last=len(tokens),kind='container',container='root',bindings={})]
    for n in nodes[1:]:
        kind='container' if n['container'] is not None else 'local' if n['tag'].startswith('block') else 'function' if n['params'] is not None else None
        if kind:scopes.append(dict(first=n['first'] if kind!='function' else (n['name'] if n['name'] is not None else n['main'])+1,last=n['last'],kind=kind,container=n.get('container'),bindings={}))
        for capture in n.get('captures') or []:scopes.append(dict(first=capture['first'],last=capture['last'],kind='capture',container=None,bindings={}))
    def chain(ti):return sorted((s for s in scopes if s['first']<=ti<=s['last']),key=lambda s:(s['last']-s['first'],s['first']))
    def owner(ti):return chain(ti)[0]
    def text(ti):return tokens[ti]['text']
    def mark(ti,role,decl=False):
        if ti is not None and tokens[ti]['tag']=='identifier' and not tokens[ti]['primitive']:roles[ti]=(role,decl)
    def bind(ti,role,scope=None):
        if ti is not None:(scope or owner(ti))['bindings'][text(ti)]=role
    def resolve(ti):
        for scope in chain(ti):
            if text(ti) in scope['bindings']:return scope['bindings'][text(ti)]
        return 'variable'
    def imported(i):
        if i is None:return False
        n=nodes[i]
        return n['tag'].startswith('builtin_call') and text(n['main'])=='@import' or n['left'] is not None and imported(n['left'])
    for n in nodes:
        if n['name'] is None:continue
        if n['params'] is not None:mark(n['name'],'function',True);bind(n['name'],'function');features.add('functions')
        elif n['tag'].endswith('var_decl'):
            init=nodes[n['init']] if n['init'] is not None else None
            role='enum' if init and init['container']=='keyword_enum' else 'type' if init and (init['container'] is not None or init['tag']=='error_set_decl') else 'namespace' if imported(n['init']) else 'constant' if owner(n['name'])['kind']=='container' and text(n['main'])=='const' else 'variable'
            mark(n['name'],role,True);bind(n['name'],role)
    for n in nodes:
        if n['params'] is not None:
            for p in n['params']:
                typ=nodes[p['type_node']] if p['type_node'] is not None else None
                role='type-parameter' if typ and text(typ['main'])=='type' and p['comptime_token'] is not None and text(p['comptime_token'])=='comptime' else 'parameter'
                mark(p['name'],role,True)
                # Pick the widest same-name function scope, including its body.
                matching=[s for s in scopes if s['kind']=='function' and s['first']==(n['name'] if n['name'] is not None else n['main'])+1]
                bind(p['name'],role,max(matching,key=lambda s:s['last']) if matching else owner(p['name']))
        if n['tag'].startswith('container_field') and n['name'] is not None:
            scope=owner(n['name']);enum=scope.get('container')=='keyword_enum'
            if enum or not n['tuple_field']:mark(n['name'],'enum-member' if enum else 'property',True);bind(n['name'],'enum-member' if enum else 'property',scope)
        for cap in n.get('captures') or []:mark(cap['name'],'variable',True);bind(cap['name'],'variable');features.add('captures')
        if n['label'] is not None:mark(n['label'],'label',n['tag'] not in {'break','continue'})
        if n['tag'].startswith('block') and n['first']<n['main'] and tokens[n['first']]['tag']=='identifier' and tokens[n['first']+1]['tag']=='colon':mark(n['first'],'label',True)
        if n['container'] is not None and n['container']!='root':features.add('containers')
        if n['tag']=='error_set_decl':
            features.add('errors')
            for ti in range(n['first'],n['last']+1):
                if tokens[ti]['tag']=='identifier':mark(ti,'enum-member',True)
        if n['tag']=='error_value':mark(n['last'],'enum-member');features.add('errors')
        if n['tag']=='enum_literal':mark(n['main'] if tokens[n['main']]['tag']=='identifier' else n['main']+1,'enum-member')
        for ti in n.get('fields') or []:mark(ti,'property')
        if n['tag']=='field_access':
            left=nodes[n['left']];role='enum-member' if left['tag']=='identifier' and resolve(left['main'])=='enum' else 'property';mark(n['name'],role)
    def type_names(i):
        if i is None:return
        n=nodes[i]
        if n['tag']=='identifier':
            ti=n['main'];r=resolve(ti);mark(ti,r if r in {'type','enum','type-parameter'} else 'type')
        elif n['tag']=='field_access':mark(n['name'],'type')
        elif n['child_type'] is not None:type_names(n['child_type'])
    for n in nodes:
        if not(n['tag'].startswith('container_field') and owner(n['main']).get('container')=='keyword_enum'):type_names(n['type_node'])
        for p in n.get('params') or []:type_names(p['type_node'])
    for n in nodes:
        if n['callee'] is None:continue
        target=nodes[n['callee']]
        if target['tag']=='field_access':mark(target['name'],'function')
        elif target['tag']=='identifier':
            ti=target['main'];r=resolve(ti);known=any(text(ti) in s['bindings'] for s in chain(ti));mark(ti,r if r in {'type','enum','type-parameter','parameter'} or known and r in {'variable','constant'} else 'function')
    units={0:0};b=u=0
    for char in source:b+=len(char.encode());u+=2 if ord(char)>0xffff else 1;units[b]=u
    spans=[];cursor=0
    def add(a,b,role,decl=False):
        if a not in units or b not in units:raise ValueError('Zig token split Unicode')
        if b<=a:return
        item=dict(start=units[a],end=units[b],tokenType=role)
        if decl:item['modifiers']=['declaration']
        spans.append(item)
    if source.startswith('\ufeff'):add(0,3,'punctuation');cursor=3
    def gap(a,b):
        while a<b:
            if raw[a:a+1] in b' \t\r\n':a+=1;continue
            if raw[a:a+2]==b'//':
                end=a+2
                while end<b and raw[end:end+1] not in b'\r\n':end+=1
                add(a,end,'comment');a=end;continue
            raise ValueError('Unmapped original Zig source gap')
    for ti,t in enumerate(tokens):
        if t['start']<cursor and t['tag']!='eof':raise ValueError('Overlapping Zig tokens')
        gap(cursor,t['start']);cursor=t['end']
        if t['tag']=='eof':continue
        tag=t['tag'];decl=False
        if tag in {'invalid','invalid_periodasterisks'}:raise ValueError('Invalid current Zig token')
        if tag.startswith('keyword_') or t['primitive'] or t['text']=='_':role='keyword'
        elif tag=='identifier':role,decl=roles.get(ti,(resolve(ti),False))
        elif tag=='builtin':role='function';features.add('builtins')
        elif tag in {'string_literal','multiline_string_literal_line','char_literal'}:role='string'
        elif tag in {'doc_comment','container_doc_comment'}:role='comment'
        elif tag=='number_literal':role='number'
        elif tag in PUNCTUATION:role='punctuation'
        else:role='operator'
        if tag in {'keyword_comptime','keyword_anytype','keyword_inline'}:features.add('comptime')
        add(t['start'],t['end'],role,decl)
    gap(cursor,len(raw))
    if '\r\n' in source:features.add('crlf')
    if any(ord(c)>127 for c in source):features.add('unicode')
    return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
