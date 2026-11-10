"""Offline Rust CST and source-local bindings; no Cargo, macros or source execution."""
from __future__ import annotations
from .parser import parser, Node
from .tools import provenance

IDENTIFIERS={'identifier','type_identifier','field_identifier','shorthand_field_identifier'}
KEYWORDS=set('as async await break const continue crate dyn else enum extern false fn for gen if impl in let loop macro macro_rules macro_rules! _ match mod move mut pub raw ref return self Self static struct super trait true type union unsafe use where while yield try abstract become box do final override priv typeof unsized virtual'.split())
PUNCTUATION=set('{}()[];,.#')|{'::','->','=>','...','..','..='}
SCOPES={'source_file','block','function_item','function_signature_item','closure_expression','impl_item','trait_item','struct_item','enum_item','mod_item','match_arm','for_expression','if_expression','while_expression'}
DEFINITIONS={'function_item':'function','function_signature_item':'function','struct_item':'type','union_item':'type','type_item':'type','associated_type':'type','enum_item':'enum','enum_variant':'enum-member','trait_item':'trait','mod_item':'namespace','macro_definition':'function','const_item':'constant','static_item':'variable'}
STRINGS={'string_literal','raw_string_literal','char_literal'}
COMMENTS={'line_comment','block_comment','shebang'}


def label(*,source,document_kind='rust',profile='rust'):
    if document_kind!='rust' or profile!='rust' or '\0' in source:raise ValueError('Expected original Rust source')
    raw=source.encode();tree=parser().parse(raw);roles={};scopes=[];features=set()
    # Repetition separators are hidden by this grammar. Recover only explicit
    # punctuation/operator gaps owned by those CST nodes, never arbitrary code.
    separators=PUNCTUATION|{'!','?','+','-','*','/','%','&','|','^','=',':','<','>','&&','||','==','!='}
    for n in list(tree.descendants()):
        if n.kind not in {'token_repetition','token_repetition_pattern'}:continue
        cursor=n.start;extra=[]
        for child in n.children:
            a,b=cursor,child.start
            while a<b and raw[a:a+1] in b' \t\r\n':a+=1
            while b>a and raw[b-1:b] in b' \t\r\n':b-=1
            if a<b:
                text=raw[a:b].decode()
                if text not in separators:raise ValueError('Unsupported Rust macro repetition separator')
                extra.append(Node(text,a,b,False,parent=n,raw=raw))
            cursor=child.end
        n.children=sorted(n.children+extra,key=lambda x:x.start)
    enum_names={n.fields['name'].text:{x.fields['name'].text for x in n.descendants() if x.kind=='enum_variant'} for n in tree.descendants() if n.kind=='enum_item'}
    def mark(n,role,decl=False):
        if n is not None:roles[n.start]=(role,decl)
    def bind(n,role):
        if n is not None:scopes[-1][n.text]=role
    def resolve(n):
        for scope in reversed(scopes):
            if n.text in scope:return scope[n.text]
        return 'variable'
    def names(n):return [] if n is None else [x for x in n.descendants() if x.kind in IDENTIFIERS]
    def last(n):
        a=names(n);return a[-1] if a else None
    def type_names(n,forced=None):
        if n is None:return
        if n.kind=='lifetime':mark(n,'type-parameter');features.add('lifetimes');return
        if n.kind in {'identifier','type_identifier'}:
            r=resolve(n);mark(n,forced or (r if r in {'type','enum','trait','type-parameter'} else 'type'));return
        if n.kind in {'scoped_identifier','scoped_type_identifier'}:
            for x in names(n.fields.get('path')):mark(x,'namespace')
            type_names(n.fields.get('name'),forced);return
        for child in n.children:type_names(child,forced)
    def pattern(n,role='variable'):
        if n is None:return
        if n.kind in {'identifier','shorthand_field_identifier'}:
            # Existing enum variants/constants in patterns are references.
            r=resolve(n)
            if r in {'enum-member','constant'}:mark(n,r)
            else:mark(n,role,True);bind(n,role)
            return
        if n.kind in {'scoped_identifier','scoped_type_identifier'}:
            return
        if n.kind in {'struct_pattern','tuple_struct_pattern'}:type_names(n.fields.get('type'))
        if n.kind=='field_pattern':
            target=n.fields.get('pattern')
            if target is not None:mark(n.fields.get('name'),'property');pattern(target,role)
            else:pattern(n.fields.get('name'),role)
            return
        for child in n.children:
            if child is not n.fields.get('type') and child.kind not in {'field_identifier','type_identifier','lifetime'}:pattern(child,role)
    def precollect(n):
        for child in n.children:
            if child.kind in DEFINITIONS:bind(child.fields.get('name'),DEFINITIONS[child.kind])
            elif child.kind in {'declaration_list','enum_variant_list'}:precollect(child)
    def visit(n):
        scoped=n.kind in SCOPES
        if scoped:scopes.append({});precollect(n)
        if n.kind in DEFINITIONS:
            role=DEFINITIONS[n.kind];name=n.fields.get('name');mark(name,role,True);bind(name,role)
            if n.kind.startswith('function_'):features.add('functions')
            if n.kind in {'struct_item','union_item'}:features.add('structs')
            if n.kind in {'trait_item','impl_item'}:features.add('traits')
            if n.kind=='enum_item':features.add('enums')
            if n.kind=='macro_definition':features.add('macros')
        if n.kind=='parameter':pattern(n.fields.get('pattern'),'parameter')
        elif n.kind=='self_parameter':
            for child in n.children:
                if child.kind=='self':mark(child,'parameter',True);bind(child,'parameter')
        elif n.kind=='closure_parameters':
            for child in n.children:
                if child.kind!='parameter':pattern(child,'parameter')
            features.add('closures')
        elif n.kind in {'let_declaration','let_condition'}:pattern(n.fields.get('pattern'));features.add('patterns')
        elif n.kind=='for_expression':pattern(n.fields.get('pattern'));features.add('patterns')
        elif n.kind=='match_arm':
            pat=n.fields.get('pattern')
            if pat is not None:
                for child in pat.children:
                    if child is not pat.fields.get('condition'):pattern(child)
            features.add('patterns')
        elif n.kind=='field_declaration':mark(n.fields.get('name'),'property',True)
        elif n.kind=='type_parameter':mark(n.fields.get('name'),'type-parameter',True);bind(n.fields.get('name'),'type-parameter');features.add('generics')
        elif n.kind=='const_parameter':mark(n.fields.get('name'),'constant',True);bind(n.fields.get('name'),'constant');features.add('generics')
        elif n.kind=='lifetime':mark(n,'type-parameter',n.parent.kind in {'lifetime_parameter','for_lifetimes'});features.add('lifetimes')
        elif n.kind=='label':mark(n,'label',n.parent.kind not in {'break_expression','continue_expression'})
        elif n.kind=='metavariable':mark(n,'parameter',n.parent.kind=='token_binding_pattern');features.add('macros')
        elif n.kind in IDENTIFIERS and n.start not in roles:
            r=resolve(n)
            if n.kind=='type_identifier' and r not in {'enum','trait','type-parameter'}:r='type'
            elif n.kind=='field_identifier':r='property'
            mark(n,r)
        elif n.kind=='self' and n.start not in roles and resolve(n)=='parameter':mark(n,'parameter')
        for child in n.children:visit(child)
        if n.kind in {'scoped_identifier','scoped_type_identifier'}:
            for x in names(n.fields.get('path')):
                if x.start not in roles or roles[x.start][0]=='variable':mark(x,'namespace')
        if n.kind=='scoped_identifier':
            target=n.fields.get('name');path=last(n.fields.get('path'))
            if target is not None and path is not None and resolve(path)=='enum' and target.text in enum_names.get(path.text,set()):mark(target,'enum-member')
        if n.kind=='impl_item':type_names(n.fields.get('trait'),'trait');type_names(n.fields.get('type'));features.add('traits')
        if n.kind in {'function_item','function_signature_item','parameter','let_declaration','const_item','static_item','field_declaration','type_item','associated_type','reference_type','pointer_type','bounded_type','generic_type','type_binding'}:
            type_names(n.fields.get('type'));type_names(n.fields.get('return_type'))
        if n.kind=='trait_bounds':
            for child in n.children:type_names(child)
        if n.kind=='struct_expression':type_names(n.fields.get('name'))
        if n.kind=='call_expression':
            target=n.fields.get('function')
            if target is not None and target.kind=='generic_function':target=target.fields.get('function')
            leaf=target.fields.get('field') if target is not None and target.kind=='field_expression' else last(target)
            if leaf is not None:
                role=roles.get(leaf.start,('variable',False))[0]
                known=any(leaf.text in s for s in scopes)
                if role not in {'parameter','type','enum','enum-member'} and not (role=='variable' and known):mark(leaf,'function')
        if n.kind=='macro_invocation':mark(last(n.fields.get('macro')),'function');features.add('macros')
        if n.kind=='use_declaration':
            for x in names(n):mark(x,'namespace')
            features.add('modules')
        if n.kind=='attribute':
            for x in names(n):mark(x,'decorator')
            features.add('attributes')
        if n.kind=='token_binding_pattern':
            for x in n.children:
                if x.kind=='fragment_specifier':mark(x,'keyword')
        if n.kind=='async_block' or n.text in {'async','await'} and not n.children:features.add('async')
        if scoped:scopes.pop()
    visit(tree)
    units={0:0};byte=unit=0
    for char in source:byte+=len(char.encode());unit+=2 if ord(char)>0xffff else 1;units[byte]=unit
    spans=[dict(start=0,end=1,tokenType='punctuation')] if source.startswith('\ufeff') else []
    for n in tree.descendants():
        if n.children or n.end==n.start or not n.text.strip():continue
        if n.kind in COMMENTS:n.end-=len(n.text)-len(n.text.rstrip('\r\n'))
        if n.start not in units or n.end not in units:raise ValueError('Rust parser split a Unicode character')
        text=n.text;mods=[]
        if n.start in roles:
            role,decl=roles[n.start]
            if decl:mods=['declaration']
        elif text in KEYWORDS or n.kind in {'primitive_type','mutable_specifier','boolean_literal','fragment_specifier'}:role='keyword'
        elif n.kind in STRINGS:role='string'
        elif n.kind in COMMENTS:role='comment'
        elif n.kind in {'integer_literal','float_literal'}:role='number'
        elif text in PUNCTUATION:role='punctuation'
        elif not n.named:role='operator'
        else:raise ValueError('Unmapped Rust lexical node: '+n.kind)
        span=dict(start=units[n.start],end=units[n.end],tokenType=role)
        if mods:span['modifiers']=mods
        spans.append(span)
    spans.sort(key=lambda s:s['start']);end=0
    encoded=source.encode('utf-16-le')
    for s in spans:
        if s['start']<end or encoded[end*2:s['start']*2].decode('utf-16-le').strip():raise ValueError('Incomplete/overlapping original Rust Gold')
        end=s['end']
    if encoded[end*2:].decode('utf-16-le').strip():raise ValueError('Unmapped Rust source suffix')
    if '\r\n' in source:features.add('crlf')
    if any(ord(x)>127 for x in source):features.add('unicode')
    return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
