"""Offline PHP syntax/local binding labels; no PHP/Composer/project execution."""
from __future__ import annotations
import re
from .parser import parser
from .tools import provenance

KEYWORDS=set('abstract and array as bool break callable case catch class clone const continue declare default die do echo else elseif empty enddeclare endfor endforeach endif endswitch endwhile enum eval exit extends false final finally float fn for foreach from function global goto if implements include include_once instanceof insteadof int interface isset iterable list match mixed namespace never new null object or parent print private protected public readonly require require_once return self static string switch throw trait true try unset use var void while xor yield __CLASS__ __DIR__ __FILE__ __FUNCTION__ __LINE__ __METHOD__ __NAMESPACE__ __TRAIT__'.split())
FUNCTIONS={'function_definition','method_declaration','anonymous_function','arrow_function'}
CLASS_ROLES={'class_declaration':'class','interface_declaration':'interface','trait_declaration':'trait','enum_declaration':'enum'}
SCOPES={'program','namespace_definition',*CLASS_ROLES,*FUNCTIONS}
PUNCTUATION=set('(){}[],;')|{'#[', '#', '\\'}
PARAMETERS={'simple_parameter','variadic_parameter','property_promotion_parameter'}


def label(*,source,document_kind='php',profile='php'):
    if document_kind!='php' or profile!='php' or '\0' in source:raise ValueError('Expected original PHP source')
    raw=source.encode();prefix=source.lstrip('\ufeff \t\r\n')
    # This choice is an offline Gold concern. Invalid tagless PHP is never
    # reinterpreted as valid HTML to inflate coverage; runtime does not use it.
    only=not prefix.startswith('<')
    tree=parser(only).parse(raw);roles={};features=set();scopes=[]
    def mark(node,role,declaration=False):
        if node is not None:roles[node.start]=(role,declaration)
    def leaves(node):return [] if node is None else [n for n in node.descendants() if n.kind in {'name','variable_name'}]
    def last(node):
        values=leaves(node);return values[-1] if values else None
    def mark_name(node,role,declaration=False):mark(last(node),role,declaration)
    def resolve(text):
        for scope in reversed(scopes):
            if text in scope:return scope[text]
        return 'variable' if text.startswith('$') else 'constant'
    def bind(node,role):
        if node is not None:scopes[-1][node.text]=role
    def collect(node):
        for child in node.children:
            if child.kind in CLASS_ROLES:bind(last(child.fields.get('name')),CLASS_ROLES[child.kind])
            elif child.kind in {'function_definition','method_declaration'}:bind(last(child.fields.get('name')),'function')
            elif child.kind=='namespace_definition':collect(child)
            elif child.kind=='declaration_list':collect(child)
    def type_names(node,role=None):
        if node is None:return
        if node.kind=='name':
            found=resolve(node.text);mark(node,role or (found if found in {'class','interface','trait','enum'} else 'type'));return
        if node.kind=='qualified_name':type_names(last(node),role);return
        for child in node.children:type_names(child,role)
    def assign_names(node):
        if node is None:return []
        if node.kind=='variable_name':return [node]
        if node.kind in {'list_literal','array_creation_expression','array_element_initializer','by_ref'}:
            return [n for c in node.children for n in assign_names(c)]
        return []
    def declare_variable(node,role='variable'):
        found=resolve(node.text)
        exists=any(node.text in s for s in scopes)
        mark(node,found if exists else role,not exists);bind(node,found if exists else role)
    def visit(node):
        if node.kind in SCOPES:scopes.append({});collect(node)
        if node.kind in CLASS_ROLES:
            name=last(node.fields.get('name'));role=CLASS_ROLES[node.kind];mark(name,role,True);bind(name,role);features.add('classes')
        elif node.kind in {'function_definition','method_declaration'}:
            name=last(node.fields.get('name'));role='constructor' if name is not None and name.text.lower() in {'__construct','__destruct'} else 'function';mark(name,role,True);bind(name,role);features.add('functions')
        elif node.kind in PARAMETERS:
            name=last(node.fields.get('name'));mark(name,'parameter',True);bind(name,'parameter')
        elif node.kind=='namespace_definition':
            for name in leaves(node.fields.get('name')):mark(name,'namespace',True);bind(name,'namespace')
            features.add('namespaces')
        elif node.kind=='namespace_use_clause':
            text=node.parent.text.lstrip();role='function' if text.startswith('use function ') else 'constant' if text.startswith('use const ') else 'class'
            alias=node.fields.get('alias');target=next((c for c in node.children if c is not alias and c.kind in {'name','qualified_name','namespace_name'}),None)
            mark_name(target,role);mark(alias,role,True);bind(alias or last(target),role)
        elif node.kind=='property_element':
            name=last(node.fields.get('name')) or next((c for c in node.children if c.kind=='variable_name'),None);mark(name,'property',True)
        elif node.kind=='const_element':
            name=next((c for c in node.children if c.kind=='name'),None);mark(name,'constant',True);bind(name,'constant')
        elif node.kind=='enum_case':
            name=last(node.fields.get('name'));mark(name,'enum-member',True);bind(name,'enum-member')
        elif node.kind in {'assignment_expression','reference_assignment_expression'}:
            for name in assign_names(node.fields.get('left')):declare_variable(name)
        elif node.kind=='foreach_statement':
            seen_as=False
            for child in node.children:
                if child.text=='as':seen_as=True
                elif seen_as and child.text in {')',':'}:break
                elif seen_as and child.kind not in {'compound_statement',')',':'}:
                    for name in child.descendants():
                        if name.kind=='variable_name':declare_variable(name)
            features.add('loops')
        elif node.kind=='catch_clause':
            name=node.fields.get('name');mark(name,'variable',True);bind(name,'variable')
        elif node.kind=='named_label_statement':mark_name(node,'label',True)
        elif node.kind=='goto_statement':mark_name(node,'label')
        elif node.kind=='variable_name' and node.start not in roles:mark(node,resolve(node.text))
        elif node.kind=='name' and node.start not in roles:
            role='namespace' if node.parent.kind=='namespace_name' else resolve(node.text);mark(node,role)
        if node.kind in {'anonymous_function','arrow_function'}:features.add('closures')
        if node.kind=='array_creation_expression':features.add('arrays')
        if node.kind in {'heredoc','nowdoc'}:features.add('heredocs')
        if node.kind=='text' and node.text.lstrip('\ufeff').strip():features.add('templates')
        for child in node.children:visit(child)
        for field in ['type','return_type']:type_names(node.fields.get(field))
        if node.kind in {'base_clause','class_interface_clause','trait_use_clause'}:
            for name in leaves(node):
                if name.parent.kind!='namespace_name':type_names(name)
        if node.kind=='object_creation_expression':
            name=next((c for c in node.children if c.kind in {'name','qualified_name','relative_scope'}),None);type_names(name,'class')
        if node.kind=='function_call_expression':
            name=last(node.fields.get('function'))
            if name is not None and name.kind!='variable_name':mark(name,'function')
        if node.kind in {'member_call_expression','nullsafe_member_call_expression','scoped_call_expression'}:
            name=last(node.fields.get('name'))
            if name is not None and name.kind!='variable_name':mark(name,'function')
            type_names(node.fields.get('scope'),'class')
        if node.kind in {'member_access_expression','nullsafe_member_access_expression','scoped_property_access_expression'}:
            name=last(node.fields.get('name'))
            if name is not None:mark(name,'property')
            type_names(node.fields.get('scope'),'class')
        if node.kind=='class_constant_access_expression':
            names=leaves(node)
            if names:
                scope=names[0];role=resolve(scope.text);mark(scope,role if role in {'class','enum','interface'} else 'class')
                if len(names)>1:mark(names[-1],'enum-member' if role=='enum' else 'constant')
        if node.kind=='attribute':
            target=next((c for c in node.children if c.kind in {'name','qualified_name'}),None);mark_name(target,'decorator')
        if node.kind=='argument' and 'name' in node.fields:mark(node.fields['name'],'parameter')
        if node.kind in SCOPES:scopes.pop()
    visit(tree)
    units={0:0};byte=unit=0
    for char in source:byte+=len(char.encode());unit+=2 if ord(char)>0xffff else 1;units[byte]=unit
    spans=[dict(start=0,end=1,tokenType='punctuation')] if source.startswith('\ufeff') else []
    for node in tree.descendants():
        if node.children or node.end==node.start:continue
        if node.start==0 and node.text.startswith('\ufeff'):
            node.start+=3
            if node.end<=node.start:continue
        text=node.text
        if not text.strip():continue
        if node.kind=='comment':node.end-=len(text)-len(text.rstrip('\r\n'));text=node.text
        if node.start not in units or node.end not in units:raise ValueError('PHP parser split a Unicode character')
        modifiers=[]
        if node.start in roles:
            role,decl=roles[node.start]
            if decl:modifiers=['declaration']
        elif node.kind in {'php_tag','php_end_tag'} or text.lower() in KEYWORDS:role='keyword'
        elif node.kind=='text':role='embedded-html'
        elif node.kind=='comment':role='comment'
        elif node.kind in {'string','string_content','escape_sequence','heredoc_start','heredoc_end','nowdoc_body','nowdoc_string'}:role='string'
        elif node.kind in {'integer','float'}:role='number'
        elif text in {'"',"'",'<<<'}:role='string'
        elif node.kind in {'primitive_type','bottom_type','boolean','null'}:role='keyword'
        elif text in PUNCTUATION:role='punctuation'
        elif not node.named:role='operator'
        else:raise ValueError('Unmapped PHP lexical node: '+node.kind)
        span=dict(start=units[node.start],end=units[node.end],tokenType=role)
        if modifiers:span['modifiers']=modifiers
        spans.append(span)
    # Match the pack's declared, source-independent touching-region decoder.
    joined=[]
    for span in sorted(spans,key=lambda x:x['start']):
        if joined and span['tokenType'] in {'string','comment','embedded-html'} and joined[-1]['tokenType']==span['tokenType'] and joined[-1]['end']==span['start'] and not span.get('modifiers') and not joined[-1].get('modifiers'):joined[-1]['end']=span['end']
        else:joined.append(span)
    if '\r\n' in source:features.add('crlf')
    if any(ord(x)>127 for x in source):features.add('unicode')
    return dict(offsetEncoding='utf-16',spans=joined,features=sorted(features))
