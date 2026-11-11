"""Pinned offline Scala CST and source-local roles, without compiler execution."""
from .parser import parser,Node
from .tools import provenance
IDS={'identifier','type_identifier','operator_identifier','capture_variable'}
TYPES={'class_definition':'type','trait_definition':'type','object_definition':'type','package_object':'type','enum_definition':'enum','type_definition':'type'}
FUNCTIONS={'function_definition','function_declaration'}
SCOPES=set(TYPES)|FUNCTIONS|{'compilation_unit','template_body','with_template_body','enum_body','block','indented_block','lambda_expression','extension_definition','given_definition','case_clause','catch_clause','for_expression','type_lambda'}
PUNCT=set('{}()[];,.@:')|{'=>','?=>','<-','$','${','</','/>','<','>'}
COMMENTS={'comment','block_comment','using_directive'}
LITERALS={'string','character_literal','integer_literal','floating_point_literal','boolean_literal','null_literal','xml_string'}


def label(*,source,document_kind='scala',profile='scala'):
    if document_kind!='scala' or profile!='scala' or '\0' in source:raise ValueError('Expected original Scala source')
    raw=source.encode();tree=parser().parse(raw);roles={};scopes=[];features=set()
    def ids(n):return [] if n is None else [x for x in n.descendants() if x.kind in IDS]
    def first(n):return next(iter(ids(n)),None)
    def mark(n,role,decl=False):
        if n is not None and n.kind in IDS:roles[n.start]=(role,decl)
    def bind(n,role):
        if n is not None and n.kind in IDS:scopes[-1][n.text]=role
    def resolve(n):return next((s[n.text] for s in reversed(scopes) if n.text in s),'variable')
    def ancestor(n,kinds):
        p=n.parent
        while p is not None:
            if p.kind in kinds:return p
            p=p.parent
        return None
    def function_role(n):
        owner=ancestor(n,set(TYPES)|FUNCTIONS|{'extension_definition','given_definition','lambda_expression'})
        return 'method' if owner and owner.kind in set(TYPES)|{'extension_definition','given_definition'} else 'function'
    def variable_role(n):
        owner=ancestor(n,FUNCTIONS|{'lambda_expression','block','indented_block','template_body','with_template_body','compilation_unit','enum_body'})
        return 'property' if owner and owner.kind in {'template_body','with_template_body','enum_body'} else 'variable'
    def pattern_ids(n):
        if n is None:return []
        if n.kind=='identifier':return [n]
        if n.kind in {'stable_identifier','stable_type_identifier','type_identifier','string','character_literal','integer_literal','floating_point_literal','boolean_literal','null_literal','wildcard'}:return []
        if n.kind=='case_class_pattern':return pattern_ids(n.fields.get('pattern'))
        result=[]
        for child in n.children:
            if getattr(child,'field_name',None) in {'type','type_arguments'}:continue
            result.extend(pattern_ids(child))
        return result
    def type_names(n):
        if n is None:return
        if n.kind in IDS:
            role=resolve(n);mark(n,role if role in {'type-parameter','enum'} else 'type');return
        if n.kind in {'arguments','annotation','string','literal_type','type_parameters'}:return
        for child in n.children:type_names(child)
    def type_parameters(n):
        for x in n.children:
            if x.kind in IDS and getattr(x,'field_name',None)=='name':mark(x,'type-parameter',True);bind(x,'type-parameter')
            elif x.kind in {'covariant_type_parameter','contravariant_type_parameter'}:mark(first(x.fields.get('name')),'type-parameter',True);bind(first(x.fields.get('name')),'type-parameter')
    def precollect(n):
        for child in n.children:
            if child.kind in TYPES:bind(first(child.fields.get('name')),TYPES[child.kind])
            elif child.kind in FUNCTIONS:bind(first(child.fields.get('name')),function_role(child))
            elif child.kind in {'val_definition','var_definition'}:
                for item in pattern_ids(child.fields.get('pattern')):bind(item,variable_role(child))
            elif child.kind in {'val_declaration','var_declaration','given_definition'}:bind(first(child.fields.get('name')),variable_role(child))
            elif child.kind in {'simple_enum_case','full_enum_case'}:bind(first(child.fields.get('name')),'enum-member')
            elif child.kind=='enum_case_definitions':precollect(child)
            elif child.kind=='type_parameters':type_parameters(child)
    enum_names={first(n.fields.get('name')).text:{first(x.fields.get('name')).text for x in n.descendants() if x.kind in {'simple_enum_case','full_enum_case'}} for n in tree.descendants() if n.kind=='enum_definition'}
    def visit(n):
        scoped=n.kind in SCOPES
        if scoped:scopes.append({});precollect(n)
        name=first(n.fields.get('name'))
        if n.kind in TYPES:mark(name,TYPES[n.kind],True);bind(name,TYPES[n.kind]);features.add('types')
        elif n.kind in FUNCTIONS:mark(name,function_role(n),True);bind(name,function_role(n));features.add('functions')
        elif n.kind=='type_parameters':type_parameters(n);features.add('generics')
        elif n.kind in {'parameter','binding','class_parameter'}:
            role='parameter'
            if n.kind=='class_parameter':
                owner=ancestor(n,{'class_definition','enum_definition','trait_definition','full_enum_case'})
                explicit=any(not c.children and c.text in {'val','var'} for c in n.children)
                case=owner and any(c.text=='case' for c in owner.children)
                if explicit or case:role='property'
            mark(name,role,True);bind(name,role)
        elif n.kind in {'val_definition','var_definition'}:
            for item in pattern_ids(n.fields.get('pattern')):mark(item,variable_role(n),True);bind(item,variable_role(n))
        elif n.kind in {'val_declaration','var_declaration','given_definition'}:mark(name,variable_role(n),True);bind(name,variable_role(n))
        elif n.kind in {'simple_enum_case','full_enum_case'}:mark(name,'enum-member',True);bind(name,'enum-member')
        elif n.kind=='lambda_expression':
            for x in pattern_ids(n.fields.get('parameters')):mark(x,'parameter',True);bind(x,'parameter')
            features.add('lambdas')
        elif n.kind in {'case_clause','catch_clause'}:
            for x in pattern_ids(n.fields.get('pattern')):mark(x,'variable',True);bind(x,'variable')
            features.add('patterns')
        elif n.kind=='enumerator':
            for child in n.children:
                if child.text in {'<-','='}:break
                for x in pattern_ids(child):mark(x,'variable',True);bind(x,'variable')
            features.add('patterns')
        if n.kind in IDS and n.start not in roles:
            if n.kind=='type_identifier':type_names(n)
            elif n.kind=='operator_identifier' and not n.text.isidentifier():mark(n,'operator')
            else:mark(n,resolve(n))
        for child in n.children:visit(child)
        if n.kind in {'type_arguments','extends_clause','derives_clause','upper_bound','lower_bound','view_bound','context_bound','projected_type','generic_type','function_type','tuple_type','compound_type','infix_type','capturing_type'}:type_names(n)
        if n.kind in {'case_class_pattern','given_pattern','typed_pattern','name_and_type'}:type_names(n.fields.get('type'))
        if n.kind in {'parameter','binding','class_parameter','val_definition','var_definition','val_declaration','var_declaration','type_definition','given_definition'}:type_names(n.fields.get('type'));type_names(n.fields.get('return_type'))
        if n.kind in {'import_declaration','export_declaration','package_identifier'}:
            for x in ids(n):mark(x,'namespace',roles.get(x.start,('',False))[1])
            features.add('imports')
        if n.kind in {'arrow_renamed_identifier','as_renamed_identifier'}:
            alias=first(n.fields.get('alias'));mark(alias,'namespace',True);bind(alias,'namespace')
        if n.kind=='field_expression':mark(first(n.fields.get('field')),'property')
        if n.kind in {'stable_identifier','stable_type_identifier'}:
            names=ids(n)
            if names:
                for x in names[1:]:mark(x,'property')
                if names[0].text in enum_names:
                    mark(names[0],'enum')
                    for x in names[1:]:mark(x,'enum-member' if x.text in enum_names[names[0].text] else 'property')
        if n.kind=='call_expression':
            target=n.fields.get('function')
            while target is not None and target.kind=='generic_function':target=target.fields.get('function')
            if target:
                leaf=first(target.fields.get('field')) if target.kind=='field_expression' else first(target)
                if leaf:
                    role=resolve(leaf)
                    if role in {'type','enum'}:mark(leaf,'constructor')
                    elif target.kind in {'field_expression','stable_identifier'}:mark(ids(target)[-1],'method')
                    elif role not in {'parameter','property'}:mark(leaf,'function')
            features.add('calls')
        if n.kind=='instance_expression':
            target=next((x for x in n.children if x.kind in {'type_identifier','stable_type_identifier','generic_type'}),None)
            if target:
                type_names(target);item=first(target.fields.get('type')) if target.kind=='generic_type' else next(iter(reversed(ids(target))),None);mark(item,'constructor')
        if n.kind=='annotation':
            names=ids(n.fields.get('name'))
            for x in names[:-1]:mark(x,'namespace')
            if names:mark(names[-1],'decorator')
        if n.kind=='assignment_expression' and n.parent and n.parent.kind=='arguments':mark(first(n.fields.get('left')),'parameter')
        if n.kind=='infix_expression':
            op=n.fields.get('operator')
            if op and op.text.isidentifier():mark(op,'method')
        if n.kind=='interpolated_string_expression':features.add('interpolation')
        if scoped:scopes.pop()
    visit(tree)
    boundaries={0:0};byte=unit=0
    for char in source:byte+=len(char.encode());unit+=2 if ord(char)>0xffff else 1;boundaries[byte]=unit
    def segment(start,end,parent):return Node('string_segment',start,end,True,parent=parent,raw=raw)
    def atoms(n):
        if n.kind in COMMENTS|LITERALS:yield n;return
        if n.kind=='interpolated_string_expression':
            shell=next((c for c in n.children if c.kind=='interpolated_string'),None)
            if shell is None:raise ValueError('Unmapped Scala interpolator shell')
            at=n.start
            for child in shell.children:
                if child.kind=='interpolation':
                    if at<child.start:yield segment(at,child.start,n)
                    yield from atoms(child);at=child.end
            if at<n.end:yield segment(at,n.end,n)
            return
        if not n.children:yield n
        else:
            for child in n.children:yield from atoms(child)
    spans=[]
    for n in atoms(tree):
        if n.start==n.end or not n.text.strip():continue
        start,end=n.start,n.end
        if n.kind in COMMENTS:end-=len(n.text)-len(n.text.rstrip('\r\n'));features.add('comments')
        if start not in boundaries or end not in boundaries:raise ValueError('Scala CST split original Unicode')
        decl=False
        if n.start in roles and n.kind!='string_segment':role,decl=roles[n.start]
        elif n.kind in COMMENTS:role='comment'
        elif n.kind in {'string','string_segment','character_literal','escape_sequence','xml_string','xml_text'}:role='string'
        elif n.kind in {'integer_literal','floating_point_literal'}:role='number'
        elif n.kind in {'boolean_literal','null_literal','wildcard','namespace_wildcard','unit'} or n.kind.endswith('_modifier') or not n.named and n.text.isidentifier():role='keyword'
        elif n.kind=='xml_name':role='property' if n.parent and n.parent.kind=='xml_attribute' else 'type'
        elif n.text in PUNCT:role='punctuation'
        elif not n.named or n.kind=='operator_identifier':role='operator'
        else:raise ValueError('Unmapped Scala lexical node: '+n.kind)
        s=dict(start=boundaries[start],end=boundaries[end],tokenType=role)
        if decl:s['modifiers']=['declaration']
        if role=='string' and spans and spans[-1]['tokenType']=='string' and spans[-1]['end']==s['start']:spans[-1]['end']=s['end']
        else:spans.append(s)
    spans.sort(key=lambda s:s['start']);end=0;encoded=source.encode('utf-16-le')
    for s in spans:
        if s['start']<end or encoded[end*2:s['start']*2].decode('utf-16-le').strip():raise ValueError('Incomplete/overlapping original Scala Gold')
        end=s['end']
    if encoded[end*2:].decode('utf-16-le').strip():raise ValueError('Incomplete Scala suffix')
    if '\r\n' in source:features.add('crlf')
    if any(ord(x)>127 for x in source):features.add('unicode')
    return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
