"""Pinned offline Ruby CST and source-local roles; no Ruby/gem execution."""
from .parser import parser,Node
from .tools import provenance
IDS={'identifier','constant','instance_variable','class_variable','global_variable','operator','hash_key_symbol'}
STRINGLIKE={'string','regex','subshell','delimited_symbol','string_array','symbol_array','heredoc_body','bare_string','bare_symbol'}
OPAQUE={'comment','simple_symbol','heredoc_beginning','heredoc_end','integer','float','rational','complex','character','uninterpreted'}
SCOPES={'program','class','module','singleton_class','method','singleton_method','block','do_block','lambda'}
PARAMS={'method_parameters','lambda_parameters','block_parameters','destructured_parameter'}
PARAM_PARTS={'optional_parameter','keyword_parameter','splat_parameter','hash_splat_parameter','block_parameter'}
PUNCT=set('{}()[];,.|:')|{'::','&.','#{','=>','...'}


def label(*,source,document_kind='ruby',profile='ruby'):
    if document_kind!='ruby' or profile!='ruby' or '\0' in source:raise ValueError('Expected original Ruby source')
    raw=source.encode();tree=parser().parse(raw);roles={};scopes=[];features=set()
    begins=[n for n in tree.descendants() if n.kind=='heredoc_beginning']
    ends=[n for n in tree.descendants() if n.kind=='heredoc_end']
    if len(begins)!=len(ends) or any(n.end<=n.start for n in ends):raise ValueError('Incomplete or empty-delimiter Ruby heredoc')
    def ids(n):return [] if n is None else [x for x in n.descendants() if x.kind in IDS]
    def first(n):return next(iter(ids(n)),None)
    def last(n):return next(iter(reversed(ids(n))),None)
    def mark(n,role,decl=False):
        if n is not None and n.kind in IDS:roles[n.start]=(role,decl)
    def bind(n,role):
        if n is not None and n.kind in {'identifier','constant','hash_key_symbol'}:scopes[-1][1][n.text]=role
    def method_context():
        return any(k in {'class','module','singleton_class','singleton_method'} for k,_ in scopes)
    def resolve(n):
        hidden=False
        for kind,scope in reversed(scopes):
            if n.text in scope and (not hidden or scope[n.text] in {'type','constant','namespace','function','method'}):return scope[n.text]
            if kind in {'class','module','singleton_class','method','singleton_method'}:hidden=True
        if n.kind=='constant':return 'constant'
        if n.kind in {'instance_variable','class_variable'}:return 'property'
        if n.kind=='global_variable':return 'variable'
        return 'method' if method_context() else 'function'
    def lhs(n):
        if n is None:return []
        if n.kind in IDS:return [n]
        if n.kind in {'call','element_reference','scope_resolution'}:return [last(n)] if n.kind=='scope_resolution' else []
        return [x for c in n.children for x in lhs(c)]
    def variable_role(n):
        if n.kind in {'instance_variable','class_variable'}:return 'property'
        return 'constant' if n.kind=='constant' else 'variable'
    def collect(n):
        for child in n.children:
            if child.kind in {'class','module'}:
                name=last(child.fields.get('name'));bind(name,'type' if child.kind=='class' else 'namespace')
            elif child.kind in {'method','singleton_method'}:bind(first(child.fields.get('name')),'method' if method_context() or child.kind=='singleton_method' else 'function')
            elif child.kind in {'assignment','operator_assignment'}:
                for x in lhs(child.fields.get('left')):bind(x,variable_role(x))
                collect(child)
            elif child.kind not in SCOPES and child.kind not in STRINGLIKE:collect(child)
    def patterns(n):
        if n is None:return
        if n.kind=='identifier':mark(n,'variable',True);bind(n,'variable');return
        if n.kind=='keyword_pattern':
            key=n.fields.get('key');value=n.fields.get('value')
            if value is None and key and key.kind=='hash_key_symbol':mark(key,'variable',True);bind(key,'variable')
            else:patterns(value)
            return
        if n.kind in {'constant','scope_resolution','expression_reference_pattern','variable_reference_pattern','string','simple_symbol'}:return
        for c in n.children:
            if getattr(c,'field_name',None)!='class':patterns(c)
    def visit(n):
        scoped=n.kind in SCOPES
        if scoped:
            scopes.append((n.kind,{}));collect(n)
            if n.kind in {'block','do_block','lambda'}:features.add('blocks')
        if n.kind in {'class','module'}:
            names=ids(n.fields.get('name'))
            for x in names[:-1]:mark(x,'namespace')
            if names:mark(names[-1],'type' if n.kind=='class' else 'namespace',True);bind(names[-1],'type' if n.kind=='class' else 'namespace')
            features.add('types')
        elif n.kind in {'method','singleton_method'}:
            name=first(n.fields.get('name'));role='method' if method_context() or n.kind=='singleton_method' else 'function';mark(name,role,True);bind(name,role);features.add('functions')
        elif n.kind in PARAMS:
            for c in n.children:
                if c.kind=='identifier':mark(c,'variable' if getattr(c,'field_name',None)=='locals' else 'parameter',True);bind(c,'variable' if getattr(c,'field_name',None)=='locals' else 'parameter')
        elif n.kind in PARAM_PARTS:
            name=n.fields.get('name');mark(name,'parameter',True);bind(name,'parameter')
        elif n.kind in {'assignment','operator_assignment'}:
            for x in lhs(n.fields.get('left')):mark(x,variable_role(x),n.kind=='assignment');bind(x,variable_role(x))
        elif n.kind=='for':
            for x in lhs(n.fields.get('pattern')):mark(x,'variable',True);bind(x,'variable')
        elif n.kind=='exception_variable':
            for x in ids(n):mark(x,'variable',True);bind(x,'variable')
        elif n.kind in {'in_clause','match_pattern','test_pattern'}:patterns(n.fields.get('pattern'));features.add('patterns')
        if n.kind in IDS and n.start not in roles:
            if n.kind=='operator':mark(n,'operator')
            elif n.kind=='hash_key_symbol':mark(n,'property')
            else:
                implicit=False
                if n.kind=='identifier' and n.text in {'_1','_2','_3','_4','_5','_6','_7','_8','_9','it'}:
                    for kind,scope in reversed(scopes):
                        if n.text in scope:break
                        if kind in {'block','do_block','lambda'}:
                            owner=n.parent
                            while owner and owner.kind not in {'block','do_block','lambda'}:owner=owner.parent
                            implicit=owner is not None and owner.fields.get('parameters') is None;break
                        if kind in {'method','singleton_method','class','module'}:break
                if n.text=='it' and any(n.text in scope for _,scope in scopes):implicit=False
                mark(n,'parameter' if implicit else resolve(n))
        for child in n.children:visit(child)
        if n.kind=='call':
            method=n.fields.get('method');receiver=n.fields.get('receiver');mark(first(method),'method' if receiver is not None or method_context() else 'function');features.add('calls')
        if n.kind=='pair':
            key=n.fields.get('key')
            if key and key.kind=='hash_key_symbol':mark(key,'parameter' if n.parent and n.parent.kind=='argument_list' else 'property')
        if n.kind=='scope_resolution':
            scope=n.fields.get('scope');name=n.fields.get('name')
            for x in ids(scope):mark(x,'namespace')
            if name and name.start not in roles:mark(name,resolve(name))
        if n.kind=='superclass':
            names=ids(n)
            for x in names[:-1]:mark(x,'namespace')
            if names:mark(names[-1],'type')
        if n.kind in {'alias','undef'}:
            for x in ids(n):mark(x,'method' if method_context() else 'function',n.kind=='alias' and x is first(n.fields.get('alias')))
        if n.kind in {'heredoc_beginning','heredoc_body'}:features.add('heredoc')
        if n.kind=='interpolation':features.add('interpolation')
        if scoped:scopes.pop()
    visit(tree)
    boundaries={0:0};byte=unit=0
    for char in source:byte+=len(char.encode());unit+=2 if ord(char)>0xffff else 1;boundaries[byte]=unit
    def holes(n):
        for c in n.children:
            if c.kind=='interpolation':yield c
            else:yield from holes(c)
    def atoms(n):
        if n.kind in OPAQUE:yield n;return
        if n.kind in STRINGLIKE:
            at=n.start
            for hole in holes(n):
                if at<hole.start:yield Node('string_segment',at,hole.start,True,parent=n,raw=raw)
                yield from atoms(hole);at=hole.end
            if at<n.end:yield Node('string_segment',at,n.end,True,parent=n,raw=raw)
            return
        if not n.children:yield n
        else:
            for c in n.children:yield from atoms(c)
    spans=[dict(start=0,end=1,tokenType='punctuation')] if source.startswith('\ufeff') else []
    for n in atoms(tree):
        if n.start==n.end or not n.text.strip():continue
        start,end=n.start,n.end
        if n.kind=='comment':end-=len(n.text)-len(n.text.rstrip('\r\n'));features.add('comments')
        if start not in boundaries or end not in boundaries:raise ValueError('Ruby CST split original Unicode')
        decl=False
        if n.start in roles and n.kind!='string_segment':role,decl=roles[n.start]
        elif n.kind in {'comment','uninterpreted'}:role='comment'
        elif n.kind in {'string_segment','heredoc_beginning','heredoc_end','character','escape_sequence'}:role='string'
        elif n.kind=='simple_symbol':role='constant'
        elif n.kind in {'integer','float','rational','complex'}:role='number'
        elif n.text=='defined?' or n.kind in {'true','false','nil','self','super','file','line','encoding'} or not n.named and n.text.isidentifier():role='keyword'
        elif getattr(n,'field_name',None)=='operator' and n.parent and n.parent.kind in {'range','binary','unary','operator_assignment'}:role='operator'
        elif n.text in PUNCT:role='punctuation'
        elif not n.named or n.kind=='operator':role='operator'
        else:raise ValueError('Unmapped Ruby lexical node: '+n.kind)
        s=dict(start=boundaries[start],end=boundaries[end],tokenType=role)
        if decl:s['modifiers']=['declaration']
        if role=='string' and spans and spans[-1]['tokenType']=='string' and spans[-1]['end']==s['start']:spans[-1]['end']=s['end']
        else:spans.append(s)
    spans.sort(key=lambda s:s['start']);end=0;encoded=source.encode('utf-16-le')
    # The grammar hides explicit backslash-newline extras. Admit only these
    # original nonliteral gap bytes; all other nonspace gaps still fail closed.
    expanded=[]
    for span in spans+[dict(start=unit,end=unit,tokenType='punctuation')]:
        if span['start']<end:raise ValueError('Overlapping original Ruby coverage')
        gap=encoded[end*2:span['start']*2].decode('utf-16-le');at=end
        for i,char in enumerate(gap):
            if not char.isspace():
                if char!='\\' or not (gap[i+1:].startswith('\n') or gap[i+1:].startswith('\r\n')):raise ValueError('Unmapped original Ruby parser gap')
                expanded.append(dict(start=at,end=at+1,tokenType='punctuation'));features.add('line-continuation')
            at+=2 if ord(char)>0xffff else 1
        if span['end']>span['start']:expanded.append(span)
        end=span['end']
    spans=expanded;end=0
    for s in spans:
        if s['start']<end or encoded[end*2:s['start']*2].decode('utf-16-le').strip():raise ValueError('Incomplete/overlapping original Ruby coverage')
        end=s['end']
    if encoded[end*2:].decode('utf-16-le').strip():raise ValueError('Incomplete Ruby suffix')
    if '\r\n' in source:features.add('crlf')
    if any(ord(x)>127 for x in source):features.add('unicode')
    return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
