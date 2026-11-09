"""Offline C grammar/local-scope teacher; no preprocessing or source execution."""
from __future__ import annotations
import re
from .parser import parser, Node
from .tools import provenance

IDENTIFIERS={'identifier','type_identifier','field_identifier','statement_identifier'}
KEYWORDS=set('auto break case char const continue default do double else enum extern float for goto if inline int long register restrict return short signed sizeof static struct switch typedef union unsigned void volatile while _Alignas _Alignof _Atomic _Bool _Complex _Generic _Imaginary _Noreturn _Static_assert _Thread_local alignas alignof bool constexpr false nullptr static_assert thread_local true typeof typeof_unqual __attribute__ __declspec'.split())
PRIMITIVE={'primitive_type','sized_type_specifier','storage_class_specifier','type_qualifier','boolean_literal','null','null_literal'}
PUNCTUATION=set('(){}[].,;')|{'...', '\\'}
SCOPE={'translation_unit','compound_statement','function_definition','function_declarator','preproc_function_def','for_statement'}
LEXER=re.compile(r'''(?P<space>\s+)|(?P<comment>//[^\r\n]*|/\*[\s\S]*?\*/)|(?P<string>(?:u8|L|u|U)?"(?:\\[\s\S]|[^"\\])*"|(?:u8|L|u|U)?'(?:\\[\s\S]|[^'\\])*')|(?P<number>(?:0[xX][\da-fA-F]+(?:\.[\da-fA-F]*)?(?:[pP][+-]?\d+)?|0[bB][01]+|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)[uUlLfF]*)|(?P<identifier>(?:[^\W\d]|_|\\u[\da-fA-F]{4}|\\U[\da-fA-F]{8})(?:\w|\\u[\da-fA-F]{4}|\\U[\da-fA-F]{8})*)|(?P<operator>##|>>=|<<=|\.\.\.|->|\+\+|--|<<|>>|<=|>=|==|!=|&&|\|\||[+*/%&|^!~<>=?:-]=?|\#)|(?P<punctuation>[(){}\[\].,;\\])''',re.UNICODE)


def declarator_name(node):
    if node is None:return None
    if node.kind in IDENTIFIERS:return node
    nested=node.fields.get('declarator')
    if nested is not None:return declarator_name(nested)
    for child in node.children:
        if child.kind in IDENTIFIERS or child.kind.endswith('_declarator'):
            value=declarator_name(child)
            if value is not None:return value
    return None


def function_signature(declarator):
    name=declarator_name(declarator)
    node=name.parent if name is not None else None
    while node is not None:
        if node.kind in {'pointer_declarator','array_declarator'}:return None
        if node.kind=='function_declarator':return node
        if node is declarator:break
        node=node.parent
    return None


def label(*,source,document_kind='c',profile='c'):
    if document_kind!='c' or profile!='c' or '\0' in source:raise ValueError('Expected original C source')
    raw=source.encode();tree=parser().parse(raw);roles={};features=set();scopes=[]
    # Preprocessor replacement lists are opaque in the CST. Tokenize only those
    # original ranges offline; never run cpp or use this lexer at inference.
    for node in list(tree.descendants()):
        if node.kind!='preproc_arg' or node.parent.kind not in {'preproc_def','preproc_function_def'}:continue
        text=node.text;cursor=0;offsets=[0]
        for char in text:offsets.append(offsets[-1]+len(char.encode()))
        while cursor<len(text):
            match=LEXER.match(text,cursor)
            if not match:raise ValueError('Unsupported macro replacement token')
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
    def declarations(node):return [c for c in node.children if getattr(c,'field_name',None)=='declarator']
    def is_function(decl):return function_signature(decl) is not None
    def precollect(node):
        for child in node.children:
            if child.kind=='function_definition':bind(declarator_name(child.fields.get('declarator')),'function')
            elif child.kind in {'declaration','type_definition'}:
                for decl in declarations(child):bind(declarator_name(decl),'type' if child.kind=='type_definition' else 'function' if is_function(decl) else 'variable')
            elif child.kind in {'preproc_def','preproc_function_def'}:bind(child.fields.get('name'),'function' if child.kind=='preproc_function_def' else 'variable')
            elif child.kind.startswith('preproc_'):precollect(child)
    def type_names(node):
        if node is None:return
        if node.kind in {'identifier','type_identifier'}:mark(node,'type');return
        # An inline type body has its own field/enumerator declarations.
        if node.kind in {'struct_specifier','union_specifier','enum_specifier'}:return
        for child in node.children:type_names(child)
    def visit(node):
        scoped=node.kind in SCOPE
        if scoped:scopes.append({});precollect(node)
        if node.kind=='function_definition':
            decl=node.fields.get('declarator');name=declarator_name(decl);mark(name,'function',True);bind(name,'function');features.add('functions')
            signature=function_signature(decl)
            if signature is not None:
                params=signature.fields.get('parameters')
                if params is not None:
                    for child in params.children:
                        if child.kind=='parameter_declaration':bind(declarator_name(child.fields.get('declarator')),'parameter')
        elif node.kind in {'declaration','field_declaration','type_definition'}:
            for decl in declarations(node):
                name=declarator_name(decl)
                role='type' if node.kind=='type_definition' else 'property' if node.kind=='field_declaration' else 'function' if is_function(decl) else 'variable'
                mark(name,role,True)
                if role!='property':bind(name,role)
            if node.kind=='type_definition':features.add('typedefs')
        elif node.kind=='parameter_declaration':
            name=declarator_name(node.fields.get('declarator'));mark(name,'parameter',True);bind(name,'parameter')
        elif node.kind in {'struct_specifier','union_specifier','enum_specifier'}:
            name=node.fields.get('name');definition='body' in node.fields
            mark(name,'enum' if definition and node.kind=='enum_specifier' else 'type',definition);bind(name,'type')
            features.add('enums' if node.kind=='enum_specifier' else 'structs')
        elif node.kind=='enumerator':mark(node.fields.get('name'),'enum-member',True);bind(node.fields.get('name'),'enum-member')
        elif node.kind in {'preproc_def','preproc_function_def'}:
            role='function' if node.kind=='preproc_function_def' else 'variable';mark(node.fields.get('name'),role,True);features.add('macros')
            if node.kind=='preproc_function_def':
                parameters=node.fields.get('parameters')
                if parameters is not None:
                    for child in parameters.children:
                        if child.kind=='identifier':mark(child,'parameter',True);bind(child,'parameter')
                    if any(child.text=='...' for child in parameters.children):scopes[-1]['__VA_ARGS__']='parameter'
        elif node.kind=='labeled_statement':mark(node.fields.get('label'),'label',True)
        elif node.kind=='goto_statement':mark(node.fields.get('label'),'label')
        elif node.kind in IDENTIFIERS and node.start not in roles:
            role='type' if node.kind=='type_identifier' else 'property' if node.kind=='field_identifier' else 'label' if node.kind=='statement_identifier' else resolve(node.text)
            if getattr(node,'macro_token',False) and role!='parameter':
                siblings=node.parent.children;index=siblings.index(node)
                if index+1<len(siblings) and siblings[index+1].text=='(':role='function'
            mark(node,role)
        for child in node.children:visit(child)
        if node.kind in {'function_definition','declaration','field_declaration','parameter_declaration','type_definition','type_descriptor','cast_expression','compound_literal_expression'}:
            type_names(node.fields.get('type'))
        if node.kind=='call_expression':
            target=node.fields.get('function')
            if target is not None and target.kind=='identifier':
                role=resolve(target.text);mark(target,role if role=='parameter' or role=='variable' and any(target.text in s for s in scopes) else 'function')
            elif target is not None and target.kind=='field_expression':mark(target.fields.get('field'),'function')
        if node.kind in {'attribute','attribute_specifier','attribute_declaration','ms_declspec_modifier'}:
            for child in node.identifiers():mark(child,'decorator')
        if node.kind=='pointer_declarator':features.add('pointers')
        if node.kind=='function_declarator':
            inner=node.fields.get('declarator')
            if inner is not None and any(n.kind=='pointer_declarator' for n in inner.descendants()):features.add('function-pointers')
        if node.kind.startswith('preproc_'):features.add('directives')
        if scoped:scopes.pop()
    visit(tree)
    units={0:0};byte=unit=0
    for char in source:byte+=len(char.encode());unit+=2 if ord(char)>0xffff else 1;units[byte]=unit
    spans=[{'start':0,'end':1,'tokenType':'punctuation'}] if source.startswith('\ufeff') else []
    leaves=[]
    for node in tree.descendants():
        if node.children or node.end==node.start or not node.text.strip():continue
        if node.kind=='comment':
            node.end-=len(node.text)-len(node.text.rstrip('\r\n'))
        leaves.append((node.start,node.end))
        if node.start not in units or node.end not in units:raise ValueError('C parser split a Unicode character')
        text=node.text;mods=[]
        if text in KEYWORDS:role='keyword'
        elif node.start in roles:
            role,decl=roles[node.start]
            if decl:mods=['declaration']
        elif node.kind in {'comment'}:role='comment'
        elif node.kind in {'string_literal','char_literal','system_lib_string','preproc_arg'}:role='string'
        elif node.kind in {'number_literal'}:role='number'
        elif node.kind in {'true','false'}:role='variable'
        elif node.kind in PRIMITIVE or text.startswith('#') and text not in {'#','##'} or not node.named and text.isidentifier():role='keyword'
        elif text in PUNCTUATION:role='punctuation'
        elif not node.named:role='operator'
        elif node.kind in {'preproc_directive'}:role='keyword'
        else:raise ValueError('Unmapped C lexical node: '+node.kind)
        span={'start':units[node.start],'end':units[node.end],'tokenType':role}
        if mods:span['modifiers']=mods
        spans.append(span)
    # The grammar skips escaped newlines between directive tokens. Preserve the
    # original continuation marker without splitting strings or comments.
    for match in re.finditer(rb'\\\r?\n',raw):
        if not any(a<=match.start()<b for a,b in leaves):
            spans.append({'start':units[match.start()],'end':units[match.start()+1],'tokenType':'punctuation'})
    if '\r\n' in source:features.add('crlf')
    if any(ord(x)>127 for x in source):features.add('unicode')
    return {'offsetEncoding':'utf-16','spans':sorted(spans,key=lambda s:s['start']),'features':sorted(features)}
