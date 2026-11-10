"""Pinned offline Dart CST and source-local roles; no SDK or project execution."""
from __future__ import annotations
from .parser import parser
from .tools import provenance

IDENTIFIERS={'identifier','type_identifier','identifier_dollar_escaped'}
TYPES={'class_declaration':'type','mixin_declaration':'type','extension_declaration':'type','extension_type_declaration':'type','enum_declaration':'enum'}
SCOPES=set(TYPES)|{'source_file','class_body','enum_body','extension_body','function_declaration','external_function_declaration','getter_declaration','setter_declaration','method_declaration','local_function_declaration','function_expression','block','for_statement','for_element','if_statement','switch_statement_case','switch_expression_case','catch_clause','type_alias'}
SIGNATURES={'function_signature','getter_signature','setter_signature','constructor_signature','constant_constructor_signature','factory_constructor_signature','redirecting_factory_constructor_signature'}
COMMENTS={'comment','documentation_comment','block_comment','documentation_block_comment','script_tag'}
PUNCTUATION=set('{}()[];,.@:')|{'=>','...','...?'}

def label(*,source,document_kind='dart',profile='dart'):
    if document_kind!='dart' or profile!='dart' or '\0' in source:raise ValueError('Expected original Dart source')
    raw=source.encode('utf-8');tree=parser().parse(raw);roles={};scopes=[];features=set()
    def ids(n):return [] if n is None else [x for x in n.descendants() if x.kind in IDENTIFIERS]
    def first(n):return next(iter(ids(n)),None)
    def last(n):return next(iter(reversed(ids(n))),None)
    def mark(n,role,decl=False):
        if n is not None:
            if n.kind not in IDENTIFIERS:raise ValueError('Expected original Dart identifier')
            roles[n.start]=(role,decl)
    def bind(n,role):
        if n is not None and not (n.text=='_' and role in {'variable','parameter'}):scopes[-1][n.text]=role
    def resolve(n):
        for scope in reversed(scopes):
            if n.text in scope:return scope[n.text]
        return 'variable'
    def ancestor(n,kinds):
        p=n.parent
        while p is not None:
            if p.kind in kinds:return p
            p=p.parent
        return None
    def signature_role(n):
        if 'constructor' in n.kind:return 'constructor'
        if n.kind in {'getter_signature','setter_signature'}:return 'property'
        owner=ancestor(n,{'method_declaration','member_declaration','local_function_declaration','function_declaration','external_function_declaration'})
        return 'method' if owner is not None and owner.kind in {'method_declaration','member_declaration'} else 'function'
    def type_names(n):
        if n is None:return
        if n.kind in {'annotation','arguments','formal_parameter_list','parameter_type_list'}:return
        if n.kind in IDENTIFIERS:
            r=resolve(n);mark(n,r if r in {'enum','type-parameter'} else 'type');return
        if n.kind=='qualified_name':
            names=ids(n)
            for item in names[:-1]:mark(item,'namespace')
            if names:type_names(names[-1])
            return
        if n.kind in {'typed_identifier','record_type_field'}:
            type_names(n.fields.get('type'));mark(n.fields.get('name'),'parameter');return
        for child in n.children:type_names(child)
    def variable_role(n):
        owner=ancestor(n,{'local_variable_declaration','top_level_variable_declaration','member_declaration'})
        if owner is None:return 'variable'
        cursor=n;start=first(n.fields.get('name')).start if first(n.fields.get('name')) else n.start
        while cursor is not None:
            if any(not c.children and c.text=='const' and c.end<=start for c in cursor.children):return 'constant'
            if cursor is owner:break
            cursor=cursor.parent
        return 'property' if owner.kind=='member_declaration' else 'variable'
    def precollect(n):
        for child in n.children:
            if child.kind in TYPES:bind(first(child.fields.get('name')),TYPES[child.kind])
            elif child.kind=='type_alias':bind(next((x for x in child.children if x.kind=='type_identifier'),None),'type')
            elif child.kind in SIGNATURES:
                if signature_role(child)!='constructor':bind(first(child.fields.get('name')),signature_role(child))
                for part in child.children:
                    if part.kind=='type_parameters':
                        for parameter in part.children:
                            if parameter.kind=='type_parameter':bind(first(parameter.fields.get('name')),'type-parameter')
            elif child.kind=='type_parameters':
                for parameter in child.children:
                    if parameter.kind=='type_parameter':bind(first(parameter.fields.get('name')),'type-parameter')
            elif child.kind=='enum_entry':bind(first(child.fields.get('name')),'enum-member')
            elif child.kind in {'initialized_identifier','initialized_variable_declaration','static_final_declaration'}:bind(first(child.fields.get('name')),variable_role(child))
            elif child.kind in {'function_declaration','local_function_declaration','getter_declaration','setter_declaration','external_function_declaration','method_declaration','member_declaration','declaration','method_signature','top_level_variable_declaration','initialized_identifier_list','static_final_declaration_list'}:precollect(child)
    enum_names={first(n.fields.get('name')).text:{x.fields['name'].text for x in n.descendants() if x.kind=='enum_entry'} for n in tree.descendants() if n.kind=='enum_declaration'}
    def visit(n):
        scoped=n.kind in SCOPES or n.kind=='formal_parameter_list' and n.parent and n.parent.kind in {'formal_parameter','field_formal_parameter','super_formal_parameter'}
        if scoped:
            scopes.append({});precollect(n)
            if n.kind=='block' and n.parent and n.parent.kind=='try_statement':
                index=n.parent.children.index(n)
                previous=n.parent.children[index-1] if index else None
                if previous is not None and previous.kind=='catch_clause':
                    for key in ['exception','stack_trace']:bind(previous.fields.get(key),'parameter')
        name=first(n.fields.get('name'))
        if n.kind in TYPES:mark(name,TYPES[n.kind],True);bind(name,TYPES[n.kind]);features.add('classes')
        elif n.kind in SIGNATURES:
            role=signature_role(n)
            for item in ids(n.fields.get('name')):mark(item,role,True)
            if role!='constructor':bind(name,role)
            features.add('functions')
        elif n.kind=='type_alias':
            item=next((x for x in n.children if x.kind=='type_identifier'),None);mark(item,'type',True);bind(item,'type')
        elif n.kind=='type_parameter':mark(name,'type-parameter',True);bind(name,'type-parameter');features.add('generics')
        elif n.kind=='enum_entry':mark(name,'enum-member',True);bind(name,'enum-member');features.add('enums')
        elif n.kind in {'formal_parameter','field_formal_parameter','super_formal_parameter'}:
            name=name or next((x for x in n.children if x.kind=='identifier'),None)
            if name is not None:
                role='property' if n.kind in {'field_formal_parameter','super_formal_parameter'} or ancestor(n,{'primary_constructor'}) else 'parameter'
                mark(name,'keyword' if name.text=='_' and role=='parameter' else role,name.text!='_');bind(name,role)
        elif n.kind=='extension_type_representation':mark(name,'property',True);bind(name,'property')
        elif n.kind in {'initialized_identifier','initialized_variable_declaration','static_final_declaration'}:
            role=variable_role(n);mark(name,'keyword' if name and name.text=='_' and role=='variable' else role,not name or name.text!='_');bind(name,role)
        elif n.kind=='variable_pattern':mark(name,'keyword' if name and name.text=='_' else 'variable',not name or name.text!='_');bind(name,'variable');features.add('patterns')
        elif n.kind in {'for_statement','for_element'}:
            mark(name,'variable',True);bind(name,'variable')
        elif n.kind=='catch_clause':
            for key in ['exception','stack_trace']:mark(n.fields.get(key),'parameter',True);bind(n.fields.get(key),'parameter')
        elif n.kind=='import_specification':mark(n.fields.get('alias'),'namespace',True);bind(n.fields.get('alias'),'namespace');features.add('imports')
        elif n.kind in IDENTIFIERS and n.start not in roles:mark(n,resolve(n))
        for child in n.children:visit(child)
        if n.kind=='type':type_names(n)
        elif n.kind=='type_parameter':type_names(n.fields.get('bound'))
        elif n.kind in {'type_alias','interfaces','superclass','mixins','on_clause'}:
            for child in n.children:
                if child.kind=='type':type_names(child)
        if n.kind in {'member_expression','null_aware_member_expression','cascade_member_expression','cascade_null_aware_member_expression'}:
            target=last(n.fields.get('property'));obj=last(n.fields.get('object'))
            role='enum-member' if obj is not None and resolve(obj)=='enum' and target is not None and target.text in enum_names.get(obj.text,set()) else 'property'
            mark(target,role)
        if n.kind in {'call_expression','cascade_call_expression'}:
            target=n.fields.get('function') or n.fields.get('property')
            while target is not None and target.kind=='instantiation_expression':target=target.fields.get('function')
            leaf=last(target)
            if leaf is not None:
                r=resolve(leaf)
                if r in {'type','enum'}:mark(leaf,'constructor')
                elif target.kind in {'member_expression','null_aware_member_expression','cascade_member_expression'}:mark(leaf,'method')
                elif r not in {'variable','parameter','property','constant'} or not any(leaf.text in s for s in scopes):mark(leaf,'function')
        if n.kind in {'new_expression','const_object_expression','constructor_invocation'}:
            type_names(n.fields.get('type'));mark(last(n.fields.get('constructor')) or last(n.fields.get('type')),'constructor')
        if n.kind=='static_member_shorthand':
            item=first(n);mark(item,'function' if any(c.kind=='arguments' for c in n.children) else 'property')
        if n.kind=='annotation':
            names=ids(n.fields.get('name'))
            for item in names[:-1]:mark(item,'namespace')
            if names:mark(names[-1],'decorator')
            features.add('annotations')
        if n.kind=='combinator':
            for item in ids(n):mark(item,'namespace')
        if n.kind=='label':
            role='parameter' if n.parent.kind=='named_argument' else 'property'
            for item in ids(n):mark(item,role)
        if n.kind in {'break_statement','continue_statement','labeled_statement'}:
            for item in n.children:
                if item.kind=='identifier':mark(item,'label',n.kind=='labeled_statement')
        if n.kind in {'record_literal','record_type','record_pattern'}:features.add('records')
        if n.kind.endswith('_pattern') or n.kind=='switch_expression':features.add('patterns')
        if n.kind in {'list_literal','set_or_map_literal','for_element','if_element'}:features.add('collections')
        if n.kind in {'await_expression','yield_statement'} or not n.children and n.text in {'async','async*','sync*'}:features.add('async')
        if n.kind=='template_substitution':features.add('interpolation')
        if scoped:scopes.pop()
    visit(tree)
    units={0:0};byte=unit=0
    for char in source:byte+=len(char.encode());unit+=2 if ord(char)>0xffff else 1;units[byte]=unit
    spans=[dict(start=0,end=1,tokenType='punctuation')] if source.startswith('\ufeff') else []
    def atoms(n):
        if n.kind in COMMENTS or n.kind=='symbol_literal' or n.kind=='string_literal' and not any(x.kind=='template_substitution' for x in n.descendants()):yield n;return
        if not n.children:yield n
        else:
            for child in n.children:yield from atoms(child)
    for n in atoms(tree):
        if n.end==n.start or not n.text.strip():continue
        if n.kind in COMMENTS:n.end-=len(n.text)-len(n.text.rstrip('\r\n'));features.add('comments')
        if n.start not in units or n.end not in units:raise ValueError('Dart parser split an original Unicode character')
        text=n.text;mods=[]
        if n.start in roles:
            role,decl=roles[n.start]
            if decl:mods=['declaration']
        elif n.kind in COMMENTS:role='comment'
        elif n.kind in {'string_literal','symbol_literal','escape_sequence'} or n.kind.startswith('template_chars_') or n.parent and n.parent.kind.startswith(('string_literal_','raw_string_literal_')):role='string'
        elif n.kind in {'decimal_integer_literal','hex_integer_literal','decimal_floating_point_literal'}:role='number'
        elif n.kind in {'void_type','dynamic_type','null_literal','true','false'} or not n.named and text.isidentifier():role='keyword'
        elif text in PUNCTUATION:role='punctuation'
        elif n.kind.endswith('_operator') or not n.named:role='operator'
        else:raise ValueError('Unmapped Dart lexical node: '+n.kind)
        span=dict(start=units[n.start],end=units[n.end],tokenType=role)
        if mods:span['modifiers']=mods
        if role=='string' and spans and spans[-1]['tokenType']=='string' and spans[-1]['end']==span['start']:spans[-1]['end']=span['end']
        else:spans.append(span)
    spans.sort(key=lambda s:s['start']);end=0;encoded=source.encode('utf-16-le')
    for s in spans:
        if s['start']<end or encoded[end*2:s['start']*2].decode('utf-16-le').strip():raise ValueError('Incomplete/overlapping original Dart Gold')
        end=s['end']
    if encoded[end*2:].decode('utf-16-le').strip():raise ValueError('Unmapped Dart source suffix')
    if '\r\n' in source:features.add('crlf')
    if any(ord(x)>127 for x in source):features.add('unicode')
    return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
