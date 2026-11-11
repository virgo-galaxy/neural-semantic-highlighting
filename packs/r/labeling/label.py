"""Offline R CST/source-local roles; no R execution or runtime prediction repair."""
from .parser import parser
from .tools import provenance

IDS={'identifier','dots','dot_dot_i'}
LITERALS={'string','integer','float','complex','comment','true','false','null','na','inf','nan'}
PUNCT=set('(){}[],;')|{'[[',']]'}
KEYWORDS={'function','if','else','for','in','while','repeat','break','next','\\'}
LEFT={'<-','<<-','='};RIGHT={'->','->>'}


def label(*, source, document_kind='r', profile='r'):
    if document_kind!='r' or profile!='r' or '\0' in source:raise ValueError('Expected original R source')
    raw=source.encode();tree=parser().parse(raw);roles={};scopes=[];features=set()
    def mark(n,role,decl=False):
        if n is not None and n.kind in IDS:roles[n.start]=(role,decl)
    def bind(n,role):
        if n is not None and n.kind in IDS:scopes[-1][n.text]=role
    def resolve(n):
        return next((scope[n.text] for scope in reversed(scopes) if n.text in scope),'variable')
    def assignment(n):
        if n.kind!='binary_operator':return None,None,None
        op=n.fields.get('operator');text=op.text if op else ''
        if text in LEFT:return n.fields.get('lhs'),n.fields.get('rhs'),text
        if text in RIGHT:return n.fields.get('rhs'),n.fields.get('lhs'),text
        return None,None,None
    def collect(n):
        target,value,op=assignment(n)
        if op not in {'<<-','->>'} and target is not None and target.kind in IDS:
            bind(target,'function' if value and value.kind=='function_definition' else 'variable')
        if n.kind=='function_definition':return
        for child in n.children:collect(child)
    def visit(n):
        scoped=n.kind in {'program','function_definition'}
        if scoped:
            scopes.append({});collect(n.fields.get('body') if n.kind=='function_definition' else n)
            if n.kind=='function_definition':features.add('functions')
        target,value,op=assignment(n)
        if op is not None:
            if target is None or value is None:raise ValueError('Incomplete R assignment')
            features.add('assignments');role='function' if value and value.kind=='function_definition' else 'variable'
            mark(target,role,op not in {'<<-','->>'})
            if op not in {'<<-','->>'}:bind(target,role)
        if n.kind=='parameter':mark(n.fields.get('name'),'parameter',True);bind(n.fields.get('name'),'parameter')
        if n.kind=='for_statement':mark(n.fields.get('variable'),'variable',True);bind(n.fields.get('variable'),'variable')
        if n.kind in IDS and n.start not in roles:mark(n,resolve(n))
        for child in n.children:visit(child)
        if n.kind=='argument':mark(n.fields.get('name'),'parameter')
        elif n.kind=='extract_operator':
            if n.fields.get('rhs') is None:raise ValueError('Incomplete R extraction')
            mark(n.fields.get('rhs'),'property')
        elif n.kind=='namespace_operator':
            mark(n.fields.get('lhs'),'namespace');mark(n.fields.get('rhs'),'variable');features.add('namespace')
            if n.fields.get('rhs') is None:raise ValueError('Incomplete R namespace expression')
        elif n.kind=='call':
            fn=n.fields.get('function');features.add('calls')
            if fn is not None:
                target=fn.fields.get('rhs') if fn.kind in {'extract_operator','namespace_operator'} else fn
                if target is not None and target.kind in IDS:
                    role='method' if fn.kind=='extract_operator' else 'function'
                    if fn.kind!='identifier' or resolve(target) not in {'parameter'}:mark(target,role)
            args=n.fields.get('arguments')
            if args is None or not any(c.text==')' for c in args.children):raise ValueError('Incomplete R call')
        if n.kind=='binary_operator':
            op=n.fields.get('operator')
            if op and op.text in {'|>','%>%','%<>%'}:features.add('pipe')
            if op and op.text=='~':features.add('formulas')
        if n.kind in {'subset','subset2'}:features.add('collections')
        if n.kind=='string':features.add('strings')
        if scoped:scopes.pop()
    visit(tree)
    boundaries={0:0};byte=unit=0
    for char in source:byte+=len(char.encode());unit+=2 if ord(char)>0xffff else 1;boundaries[byte]=unit
    spans=[]
    def atoms(n):
        if n.kind in LITERALS or not n.children:yield n
        else:
            for child in n.children:yield from atoms(child)
    for n in atoms(tree):
        if not n.text.strip():continue
        start,end=n.start,n.end
        if n.kind=='comment':end-=len(n.text)-len(n.text.rstrip('\r\n'));features.add('comments')
        if start not in boundaries or end not in boundaries:raise ValueError('R parser split Unicode character')
        declaration=False
        if n.start in roles:role,declaration=roles[n.start]
        elif n.kind=='comment':role='comment'
        elif n.kind=='string':role='string'
        elif n.kind in {'integer','float','complex'}:role='number'
        elif n.kind in {'true','false','null','na','inf','nan','break','next'} or n.text in KEYWORDS:role='keyword'
        elif n.text in PUNCT:role='punctuation'
        elif not n.named or getattr(n,'field_name',None)=='operator':role='operator'
        else:raise ValueError('Unmapped R lexical node: '+n.kind)
        span=dict(start=boundaries[start],end=boundaries[end],tokenType=role)
        if declaration:span['modifiers']=['declaration']
        spans.append(span)
    spans.sort(key=lambda s:s['start']);last=0;encoded=source.encode('utf-16-le')
    # This grammar hides statement separators as extras. Only semicolons and
    # a leading BOM may fill original parser gaps; every other nonspace fails.
    expanded=[]
    for span in spans+[dict(start=unit,end=unit,tokenType='punctuation')]:
        gap=encoded[last*2:span['start']*2].decode('utf-16-le')
        at=last
        for char in gap:
            width=2 if ord(char)>0xffff else 1
            if not char.isspace():
                if char!=';' and not (at==0 and char=='\ufeff'):raise ValueError('Unmapped original R parser gap')
                expanded.append(dict(start=at,end=at+width,tokenType='punctuation'))
            at+=width
        if span['end']>span['start']:expanded.append(span)
        last=span['end']
    spans=expanded;last=0
    for span in spans:
        if span['start']<last or encoded[last*2:span['start']*2].decode('utf-16-le').strip():raise ValueError('Incomplete/overlapping original R coverage')
        last=span['end']
    if encoded[last*2:].decode('utf-16-le').strip():raise ValueError('Incomplete original R suffix')
    if '\r\n' in source:features.add('crlf')
    if any(ord(x)>127 for x in source):features.add('unicode')
    return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
