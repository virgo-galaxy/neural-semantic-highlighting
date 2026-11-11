"""Pinned Lua CST with ordered lexical bindings; no Lua execution or source repair."""
from .parser import parser
from .tools import provenance
SCOPES={'chunk','block','function_declaration','function_definition','for_statement','repeat_statement'}
PUNCT=set('{}()[];,.')|{':','::','<','>'}


def label(*,source,document_kind='lua',profile='lua'):
    if document_kind!='lua' or profile!='lua' or '\0' in source:raise ValueError('Expected original Lua source')
    raw=source.encode();tree=parser().parse(raw);roles={};scopes=[];features=set()
    def ids(n):return [] if n is None else [x for x in n.descendants() if x.kind=='identifier']
    def mark(n,role,decl=False):
        if n is not None and n.kind=='identifier':roles[n.start]=(role,decl)
    def binding(n):
        if n is not None:
            for scope in reversed(scopes):
                if n.text in scope:return scope,scope[n.text]
        return None,'variable'
    def bind(n,role,local=True,force_global=False):
        if n is None or n.kind!='identifier':return
        if local:scopes[-1][n.text]=role
        elif force_global:scopes[0][n.text]=role
        else:
            owner,_=binding(n);(owner if owner is not None else scopes[0])[n.text]=role
    def names(n):return [c for c in n.children if c.kind=='identifier'] if n else []
    def assignment_parts(n):
        seq=next((c for c in n.children if c.kind=='variable_list'),None);values=next((c for c in n.children if c.kind=='expression_list'),None)
        return seq,[c for c in values.children if c.named] if values else []
    def declaration_specs(seq,values,local,global_keyword=False):
        if seq is None:return []
        children=seq.children;prefix=next((c for c in children if c.kind=='attribute'),None)
        first_name=next((c for c in children if c.kind=='identifier'),None)
        prefix_const=prefix is not None and first_name is not None and prefix.start<first_name.start and any(x.text=='const' for x in ids(prefix))
        targets=[c for c in children if c.named and c.kind!='attribute'];result=[]
        for index,target in enumerate(targets):
            value=values[index] if index<len(values) else None
            if target.kind=='identifier':
                at=children.index(target);attr=children[at+1] if at+1<len(children) and children[at+1].kind=='attribute' else None
                constant=prefix_const or attr is not None and any(x.text=='const' for x in ids(attr))
                owner,prior=binding(target);role='constant' if constant else ('function' if value and value.kind=='function_definition' else ('parameter' if not local and prior=='parameter' else 'variable'))
                result.append((target,role,local or owner is None or value is not None and value.kind=='function_definition'))
            elif target.kind in {'dot_index_expression','method_index_expression'}:
                leaf=target.fields.get('field') or target.fields.get('method');fn=value is not None and value.kind=='function_definition';result.append((leaf,'method' if fn else 'property',fn))
        return result
    def visit(n):
        # A function declaration's name is visible recursively. Ordinary locals
        # become visible only after their initializer, including nested closures.
        fn_name=n.fields.get('name') if n.kind=='function_declaration' else None
        fn_target=fn_name if fn_name and fn_name.kind=='identifier' else (fn_name.fields.get('field') or fn_name.fields.get('method') if fn_name else None)
        if fn_name and fn_name.kind=='identifier':
            local=any(c.text=='local' for c in n.children if not c.named)
            force_global=any(c.text=='global' for c in n.children if not c.named)
            bind(fn_name,'function',local=local,force_global=force_global)
        scoped=n.kind in SCOPES and not (n.kind=='block' and n.parent and n.parent.kind=='repeat_statement')
        if scoped:scopes.append({})
        if n.kind in {'function_definition','function_declaration'}:
            features.add('functions')
            if n.kind=='function_definition':features.add('closures')
            if fn_name and fn_name.kind=='method_index_expression':scopes[-1]['self']='parameter'
        if n.kind=='parameters':
            for x in names(n):mark(x,'parameter',True);bind(x,'parameter')
        elif n.kind in {'for_numeric_clause','for_generic_clause'}:
            targets=[n.fields.get('name')] if n.kind=='for_numeric_clause' else names(next((c for c in n.children if c.kind=='variable_list'),None))
            for x in targets:mark(x,'variable',True)
            features.add('loops')
        elif n.kind=='attribute':
            for x in ids(n):mark(x,'keyword')
        elif n.kind in {'label_statement','goto_statement'}:
            for x in ids(n):mark(x,'label',n.kind=='label_statement')
        assignment=n.kind=='assignment_statement'
        local_decl=assignment and n.parent and n.parent.kind=='variable_declaration'
        local_keyword=bool(local_decl and any(c.text=='local' for c in n.parent.children if not c.named))
        global_keyword=bool(local_decl and any(c.text=='global' for c in n.parent.children if not c.named))
        specs=[]
        if assignment:
            seq,values=assignment_parts(n);specs=declaration_specs(seq,values,bool(local_decl),global_keyword)
            for x,role,decl in specs:mark(x,role,decl)
        elif n.kind=='variable_declaration':
            seq=next((c for c in n.children if c.kind=='variable_list'),None)
            if seq:
                specs=declaration_specs(seq,[],True);directive=any(c.text=='global' for c in n.children if not c.named) and len(names(seq))==1 and names(seq)[0].text=='none'
                if directive:specs=[(names(seq)[0],'keyword',False)]
                for x,role,decl in specs:mark(x,role,decl)
        if n.kind=='identifier' and n.start not in roles:mark(n,binding(n)[1])
        for child in n.children:visit(child)
        if n.kind in {'assignment_statement','variable_declaration'}:
            for x,role,decl in specs:
                mark(x,role,decl)
                if role!='keyword':bind(x,role,local=bool(n.kind=='variable_declaration' or local_decl and local_keyword),force_global=global_keyword)
        if n.kind in {'for_numeric_clause','for_generic_clause'}:
            for x in targets:bind(x,'variable')
        if n.kind in {'dot_index_expression','method_index_expression'}:mark(n.fields.get('field') or n.fields.get('method'),'property')
        if n.kind=='function_declaration':mark(fn_target,'function' if fn_name.kind=='identifier' else 'method',True)
        if n.kind=='function_call':
            target=n.fields.get('name')
            if target:
                if target.kind=='identifier':mark(target,'parameter' if binding(target)[1]=='parameter' else 'function')
                elif target.kind in {'dot_index_expression','method_index_expression'}:mark(target.fields.get('field') or target.fields.get('method'),'method')
            features.add('calls')
        if n.kind=='field':
            name=n.fields.get('name');value=n.fields.get('value')
            computed=any(c.text=='[' for c in n.children if not c.named)
            if name and name.kind=='identifier' and not computed:mark(name,'method' if value and value.kind=='function_definition' else 'property',value is not None and value.kind=='function_definition')
        if n.kind=='table_constructor':features.add('tables')
        if n.kind=='string':features.add('strings')
        if n.kind in {'while_statement','repeat_statement'}:features.add('loops')
        if scoped:scopes.pop()
    visit(tree)
    boundaries={0:0};byte=unit=0
    for char in source:byte+=len(char.encode());unit+=2 if ord(char)>0xffff else 1;boundaries[byte]=unit
    def atoms(n):
        if n.kind in {'string','comment','hash_bang_line','number','vararg_expression'} or not n.children:yield n
        else:
            for c in n.children:yield from atoms(c)
    spans=[dict(start=0,end=1,tokenType='punctuation')] if source.startswith('\ufeff') else []
    for n in atoms(tree):
        if n.start==n.end or not n.text.strip():continue
        start,end=n.start,n.end
        if n.kind in {'comment','hash_bang_line'}:end-=len(n.text)-len(n.text.rstrip('\r\n'));features.add('comments')
        if start not in boundaries or end not in boundaries:raise ValueError('Lua CST split original Unicode')
        decl=False
        if n.start in roles:role,decl=roles[n.start]
        elif n.kind in {'comment','hash_bang_line'}:role='comment'
        elif n.kind=='string':role='string'
        elif n.kind=='number':role='number'
        elif n.kind=='vararg_expression':role='parameter';decl=n.parent is not None and n.parent.kind=='parameters'
        elif n.kind in {'true','false','nil','break_statement'} or not n.named and n.text.isidentifier():role='keyword'
        elif getattr(n,'field_name',None)=='operator':role='operator'
        elif n.text in PUNCT:role='punctuation'
        elif not n.named:role='operator'
        else:raise ValueError('Unmapped Lua lexical node: '+n.kind)
        s=dict(start=boundaries[start],end=boundaries[end],tokenType=role)
        if decl:s['modifiers']=['declaration']
        spans.append(s)
    spans.sort(key=lambda s:s['start']);end=0;encoded=source.encode('utf-16-le')
    for s in spans:
        if s['start']<end or encoded[end*2:s['start']*2].decode('utf-16-le').strip():raise ValueError('Incomplete/overlapping original Lua coverage')
        end=s['end']
    if encoded[end*2:].decode('utf-16-le').strip():raise ValueError('Incomplete original Lua suffix')
    if '\r\n' in source:features.add('crlf')
    if any(ord(x)>127 for x in source):features.add('unicode')
    return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
