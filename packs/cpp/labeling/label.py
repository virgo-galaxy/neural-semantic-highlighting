"""Pinned C++ CST and bounded local scopes; offline supervision only."""
from __future__ import annotations
import re
from .parser import parser,Node
from .tools import provenance
IDENTIFIERS={'identifier','type_identifier','field_identifier','namespace_identifier','statement_identifier','operator_name','destructor_name'}
KEYWORDS=set('alignas alignof and and_eq asm auto bitand bitor bool break case catch char char8_t char16_t char32_t class co_await co_return co_yield compl concept const consteval constexpr constinit const_cast continue decltype default delete do double dynamic_cast else enum explicit export extern false float for friend goto if inline int long mutable namespace new noexcept not not_eq nullptr operator or or_eq private protected public register reinterpret_cast requires return short signed sizeof static static_assert static_cast struct switch template this thread_local throw true try typedef typeid typename union unsigned using virtual void volatile wchar_t while xor xor_eq __attribute__ __declspec'.split())
PRIMITIVE={'primitive_type','sized_type_specifier','storage_class_specifier','type_qualifier','boolean_literal','null','null_literal'}
PUNCTUATION=set('(){}[].,;')|{'...', '\\', '[[', ']]'}
SCOPE={'translation_unit','compound_statement','function_definition','function_declarator','preproc_function_def','for_statement','for_range_loop','class_specifier','struct_specifier','union_specifier','namespace_definition','template_declaration','lambda_expression','requires_expression','catch_clause'}
LEXER=re.compile(r'''(?P<space>\s+)|(?P<comment>//[^\r\n]*|/\*[\s\S]*?\*/)|(?P<string>(?:u8|L|u|U)?"(?:\\[\s\S]|[^"\\])*"|(?:u8|L|u|U)?'(?:\\[\s\S]|[^'\\])*')|(?P<number>(?:0[xX][\da-fA-F]+(?:\.[\da-fA-F]*)?(?:[pP][+-]?\d+)?|0[bB][01]+|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)[uUlLfF]*)|(?P<identifier>(?:[^\W\d]|_|\\u[\da-fA-F]{4}|\\U[\da-fA-F]{8})(?:\w|\\u[\da-fA-F]{4}|\\U[\da-fA-F]{8})*)|(?P<operator>##|>>=|<<=|\.\.\.|->|\+\+|--|<<|>>|<=|>=|==|!=|&&|\|\||[+*/%&|^!~<>=?:-]=?|\#)|(?P<punctuation>[(){}\[\].,;\\])''',re.UNICODE)

def declarator_name(node):
    if node is None:return None
    if node.kind in IDENTIFIERS:return node
    if node.kind in {'qualified_identifier','template_function','template_method','template_type'}:
        return declarator_name(node.fields.get('name'))
    nested=node.fields.get('declarator')
    if nested is not None:return declarator_name(nested)
    for child in node.children:
        if child.kind in IDENTIFIERS or child.kind.endswith('_declarator'):
            value=declarator_name(child)
            if value is not None:return value
    return None


def function_signature(declarator):
    name=declarator_name(declarator);node=name.parent if name is not None else None
    while node is not None:
        if node.kind in {'pointer_declarator','array_declarator'}:return None
        if node.kind=='function_declarator':return node
        if node is declarator:break
        node=node.parent
    return None


def label(*,source,document_kind='cpp',profile='cpp'):
    if document_kind!='cpp' or profile!='cpp' or '\0' in source:raise ValueError('Expected original C++ source')
    raw=source.encode();tree=parser().parse(raw);roles={};features=set();scopes=[];classes=[]
    concepts={n.fields['name'].text for n in tree.descendants() if n.kind=='concept_definition' and 'name' in n.fields}
    for node in list(tree.descendants()):
        if node.kind!='preproc_arg' or node.parent.kind not in {'preproc_def','preproc_function_def'}:continue
        text=node.text;cursor=0;offsets=[0]
        for char in text:offsets.append(offsets[-1]+len(char.encode()))
        while cursor<len(text):
            match=LEXER.match(text,cursor)
            if not match:raise ValueError('Unsupported C++ macro replacement token')
            a,b=match.span();cursor=b
            if match.lastgroup=='space':continue
            kind={'number':'number_literal','string':'string_literal','comment':'comment','identifier':'identifier'}.get(match.lastgroup,match[0])
            child=Node(kind,node.start+offsets[a],node.start+offsets[b],match.lastgroup in {'number','string','comment','identifier'},parent=node,raw=raw)
            child.macro_token=True;node.children.append(child)
    def mark(node,role,declaration=False):
        if node is not None:roles[node.start]=(role,declaration)
    def bind(node,role):
        if node is not None:scopes[-1][node.text]=role
    def resolve(name):
        for scope in reversed(scopes):
            if name in scope:return scope[name]
        return 'variable'
    def known(name):return any(name in scope for scope in scopes)
    def declarations(node):return [c for c in node.children if getattr(c,'field_name',None)=='declarator']
    def is_function(node):return function_signature(node) is not None
    def constructor(name,node):
        return name is not None and (name.kind=='destructor_name' or not node.fields.get('type') and name.kind!='operator_name')
    def binding_names(node):
        if node is None:return []
        if node.kind=='structured_binding_declarator':return node.identifiers()
        if node.kind=='init_declarator':return binding_names(node.fields.get('declarator'))
        name=declarator_name(node);return [name] if name is not None else []
    def precollect(node):
        for child in node.children:
            if child.kind=='function_definition':
                name=declarator_name(child.fields.get('declarator'))
                if not constructor(name,child):bind(name,'function')
            elif child.kind in {'declaration','field_declaration','type_definition'}:
                for decl in declarations(child):
                    for name in binding_names(decl):
                        if is_function(decl) and constructor(name,child):continue
                        bind(name,'type' if child.kind=='type_definition' else 'function' if is_function(decl) else 'property' if child.kind=='field_declaration' else 'variable')
            elif child.kind in {'class_specifier','struct_specifier','union_specifier','enum_specifier','alias_declaration','concept_definition'}:
                bind(child.fields.get('name'),'class' if child.kind=='class_specifier' else 'enum' if child.kind=='enum_specifier' else 'type')
            elif child.kind=='namespace_definition':bind(child.fields.get('name'),'namespace')
            elif child.kind in {'preproc_def','preproc_function_def'}:bind(child.fields.get('name'),'function' if child.kind=='preproc_function_def' else 'variable')
            elif child.kind.startswith('preproc_') or child.kind=='template_declaration':precollect(child)
    def type_names(node):
        if node is None:return
        if node.kind in {'identifier','type_identifier'}:
            role=resolve(node.text);mark(node,role if role in {'type-parameter','class','enum'} else 'type',roles.get(node.start,('',False))[1]);return
        if node.kind in {'struct_specifier','union_specifier','enum_specifier','class_specifier','template_argument_list','decltype'}:return
        if node.kind=='qualified_identifier':type_names(node.fields.get('name'));return
        for child in node.children:type_names(child)
    def prebind_parameters(params):
        if params is not None:
            for child in params.children:
                if child.kind in {'parameter_declaration','optional_parameter_declaration','variadic_parameter_declaration'}:bind(declarator_name(child.fields.get('declarator')),'parameter')
    def visit(node):
        scoped=node.kind in SCOPE
        if scoped:scopes.append({});precollect(node)
        class_node=node.kind in {'class_specifier','struct_specifier','union_specifier'}
        if class_node:classes.append(node.fields.get('name').text if node.fields.get('name') is not None else '')
        if node.kind=='function_definition':
            decl=node.fields.get('declarator');name=declarator_name(decl);role='constructor' if constructor(name,node) else 'function';mark(name,role,True)
            if role=='function':bind(name,role)
            features.add('functions');signature=function_signature(decl)
            if signature is not None:prebind_parameters(signature.fields.get('parameters'))
        elif node.kind in {'declaration','field_declaration','type_definition'}:
            for decl in declarations(node):
                role='type' if node.kind=='type_definition' else ('constructor' if constructor(declarator_name(decl),node) else 'function') if is_function(decl) else 'property' if node.kind=='field_declaration' else 'variable'
                for name in binding_names(decl):
                    mark(name,role,True)
                    if role!='constructor':bind(name,role)
            if node.kind=='type_definition':features.add('typedefs')
        elif node.kind in {'parameter_declaration','optional_parameter_declaration','variadic_parameter_declaration'}:
            name=declarator_name(node.fields.get('declarator'));kind=node.fields.get('type')
            role='type-parameter' if node.parent.kind=='template_parameter_list' and kind is not None and kind.text in concepts else 'parameter'
            mark(name,role,True);bind(name,role)
        elif node.kind in {'type_parameter_declaration','variadic_type_parameter_declaration','optional_type_parameter_declaration','template_template_parameter_declaration'}:
            children=[c for c in node.children if c.kind in {'type_identifier','identifier'}]
            if children:mark(children[0],'type-parameter',True);bind(children[0],'type-parameter')
        elif node.kind in {'struct_specifier','union_specifier','enum_specifier','class_specifier'}:
            name=node.fields.get('name');definition='body' in node.fields;role='class' if node.kind=='class_specifier' else 'enum' if node.kind=='enum_specifier' else 'type';mark(name,role,definition);bind(name,role);features.add('classes' if class_node else 'enums')
        elif node.kind=='enumerator':mark(node.fields.get('name'),'enum-member',True);bind(node.fields.get('name'),'enum-member')
        elif node.kind in {'namespace_definition','namespace_alias_definition'}:
            name=node.fields.get('name');mark(name,'namespace',True);bind(name,'namespace');features.add('namespaces')
        elif node.kind=='alias_declaration':mark(node.fields.get('name'),'type',True);bind(node.fields.get('name'),'type');features.add('typedefs')
        elif node.kind=='concept_definition':mark(node.fields.get('name'),'type',True);bind(node.fields.get('name'),'type');features.add('concepts')
        elif node.kind=='for_range_loop':
            for name in binding_names(node.fields.get('declarator')):mark(name,'variable',True);bind(name,'variable')
        elif node.kind=='lambda_expression':
            features.add('lambdas');decl=node.fields.get('declarator')
            if decl is not None:prebind_parameters(decl.fields.get('parameters'))
        elif node.kind=='lambda_capture_initializer':mark(node.fields.get('left'),'variable',True);bind(node.fields.get('left'),'variable')
        elif node.kind in {'preproc_def','preproc_function_def'}:
            role='function' if node.kind=='preproc_function_def' else 'variable';mark(node.fields.get('name'),role,True);features.add('macros')
            if node.kind=='preproc_function_def':
                params=node.fields.get('parameters')
                if params is not None:
                    for child in params.children:
                        if child.kind=='identifier':mark(child,'parameter',True);bind(child,'parameter')
                    if any(child.text=='...' for child in params.children):scopes[-1]['__VA_ARGS__']='parameter'
        elif node.kind=='labeled_statement':mark(node.fields.get('label'),'label',True)
        elif node.kind=='goto_statement':mark(node.fields.get('label'),'label')
        elif node.kind in IDENTIFIERS and node.start not in roles:
            role=resolve(node.text)
            if node.kind=='type_identifier' and role not in {'class','enum','type-parameter'}:role='type'
            elif node.kind=='namespace_identifier' and role not in {'type','class','enum','type-parameter'}:role='namespace'
            elif node.kind=='field_identifier':role='property'
            elif node.kind=='statement_identifier':role='label'
            elif node.kind=='operator_name':role='function'
            elif node.kind=='destructor_name':role='constructor'
            if getattr(node,'macro_token',False) and role!='parameter':
                siblings=node.parent.children;index=next(i for i,x in enumerate(siblings) if x is node)
                if index+1<len(siblings) and siblings[index+1].text=='(':role='function'
            mark(node,role)
        if node.kind=='template_declaration':features.add('templates')
        for child in node.children:visit(child)
        if node.kind in {'function_definition','declaration','field_declaration','parameter_declaration','optional_parameter_declaration','type_definition','type_descriptor','cast_expression','compound_literal_expression','new_expression','base_class_clause','alias_declaration'}:type_names(node.fields.get('type'))
        if node.kind=='call_expression':
            target=node.fields.get('function');name=declarator_name(target.fields.get('field')) if target is not None and target.kind=='field_expression' else declarator_name(target)
            if target is not None and target.kind in {'template_function','template_method'}:features.add('templates')
            if name is not None:
                role=resolve(name.text)
                if target.kind=='field_expression':role='function'
                elif role not in {'parameter','variable'} or not known(name.text):role='constructor' if role in {'class','type'} else 'function'
                mark(name,role)
            elif target is not None and target.kind=='field_expression':mark(declarator_name(target.fields.get('field')),'function')
        if node.kind in {'attribute','attribute_specifier','attribute_declaration','ms_declspec_modifier'}:
            for child in node.identifiers():mark(child,'decorator')
        if node.kind=='pointer_declarator':features.add('pointers')
        if node.kind=='raw_string_literal':features.add('raw-strings')
        if node.kind.startswith('preproc_'):features.add('directives')
        if class_node:classes.pop()
        if scoped:scopes.pop()
    visit(tree)
    units={0:0};byte=unit=0
    for char in source:byte+=len(char.encode());unit+=2 if ord(char)>0xffff else 1;units[byte]=unit
    spans=[{'start':0,'end':1,'tokenType':'punctuation'}] if source.startswith('\ufeff') else [];leaves=[]
    for node in tree.descendants():
        if node.children or node.end==node.start or not node.text.strip():continue
        if node.kind=='comment':node.end-=len(node.text)-len(node.text.rstrip('\r\n'))
        leaves.append((node.start,node.end))
        if node.start not in units or node.end not in units:raise ValueError('C++ parser split a Unicode character')
        text=node.text;mods=[]
        if text in KEYWORDS:role='keyword'
        elif node.start in roles:
            role,decl=roles[node.start]
            if decl:mods=['declaration']
        elif node.kind=='comment':role='comment'
        elif node.kind in {'string_literal','raw_string_literal','char_literal','system_lib_string','preproc_arg'}:role='string'
        elif node.kind=='number_literal':role='number'
        elif node.kind=='literal_suffix':role='function'
        elif node.kind in {'true','false'}:role='variable'
        elif node.kind in PRIMITIVE or text.startswith('#') and text not in {'#','##'} or not node.named and text.isidentifier():role='keyword'
        elif text in PUNCTUATION or text in {'<','>'} and node.parent.kind in {'template_argument_list','template_parameter_list'}:role='punctuation'
        elif not node.named:role='operator'
        elif node.kind=='preproc_directive':role='keyword'
        else:raise ValueError('Unmapped C++ lexical node: '+node.kind)
        span={'start':units[node.start],'end':units[node.end],'tokenType':role}
        if mods:span['modifiers']=mods
        spans.append(span)
    for match in re.finditer(rb'\\\r?\n',raw):
        if not any(a<=match.start()<b for a,b in leaves):spans.append({'start':units[match.start()],'end':units[match.start()+1],'tokenType':'punctuation'})
    if '\r\n' in source:features.add('crlf')
    if any(ord(x)>127 for x in source):features.add('unicode')
    return {'offsetEncoding':'utf-16','spans':sorted(spans,key=lambda s:s['start']),'features':sorted(features)}
