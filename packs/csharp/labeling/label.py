"""Offline C# syntax/local-scope Gold. No .NET, reflection or source execution."""
from __future__ import annotations
import re
from .parser import parser
from .tools import provenance

TYPES = {'class_declaration': 'class', 'record_declaration': 'class',
         'struct_declaration': 'type', 'interface_declaration': 'interface',
         'enum_declaration': 'enum', 'delegate_declaration': 'type'}
METHODS = {'method_declaration': 'method', 'local_function_statement': 'function',
           'constructor_declaration': 'constructor', 'destructor_declaration': 'constructor'}
SCOPE_KINDS = {'compilation_unit', 'namespace_declaration', 'class_declaration', 'record_declaration',
               'struct_declaration', 'interface_declaration', 'enum_declaration', 'delegate_declaration',
               'method_declaration', 'local_function_statement', 'constructor_declaration', 'destructor_declaration',
               'operator_declaration', 'conversion_operator_declaration', 'block', 'lambda_expression',
               'anonymous_method_expression', 'foreach_statement', 'for_statement', 'catch_clause', 'accessor_declaration',
               'query_expression', 'switch_expression_arm', 'switch_section'}
TYPE_CONTEXTS = {'parameter', 'variable_declaration', 'property_declaration', 'event_declaration',
                 'delegate_declaration', 'method_declaration', 'local_function_statement', 'catch_declaration',
                 'foreach_statement', 'declaration_expression', 'declaration_pattern', 'recursive_pattern',
                 'cast_expression', 'as_expression', 'type_of_expression', 'typeof_expression',
                 'sizeof_expression', 'default_expression', 'stackalloc_expression', 'array_creation_expression',
                 'object_creation_expression', 'type_parameter_constraint', 'tuple_element', 'function_pointer_parameter',
                 'conversion_operator_declaration', 'operator_declaration'}
STRINGS = {'string_literal', 'verbatim_string_literal', 'raw_string_literal', 'interpolated_string_expression', 'character_literal', 'preproc_arg'}
KEYWORD_NODES = {'modifier', 'implicit_type', 'predefined_type', 'null_literal', 'boolean_literal', 'discard', 'attribute_target_specifier'}
PUNCTUATION = set('(){}[].,;')


def symbol(text):
    text = text.removeprefix('@')
    return re.sub(r'\\(?:u([0-9a-fA-F]{4})|U([0-9a-fA-F]{8}))',
                  lambda m: chr(int(m[1] or m[2], 16)), text)


def label(*, source: str, document_kind='csharp', profile='csharp'):
    if document_kind != 'csharp' or profile != 'csharp' or '\0' in source:
        raise ValueError('Expected original C# source')
    raw = source.encode('utf-8'); tree = parser().parse(raw)
    roles, features, scopes = {}, set(), []

    def mark(node, role, declaration=False):
        if node is not None:
            if node.kind not in {'identifier', 'implicit_parameter'}:
                raise ValueError('Expected original C# identifier node')
            roles[node.start] = (role, declaration)

    def bind(node, role):
        if node is not None: scopes[-1][symbol(node.text)] = role

    def resolve(text):
        for scope in reversed(scopes):
            if symbol(text) in scope: return scope[symbol(text)]
        return 'variable'

    def type_names(node):
        if node is None: return
        if node.kind in {'attribute', 'attribute_list', 'argument_list'}: return
        if node.kind == 'tuple_element':
            type_names(node.fields.get('type')); mark(node.fields.get('name'), 'property'); return
        if node.kind in {'identifier', 'implicit_parameter'}: mark(node, 'type'); return
        for child in node.children: type_names(child)

    def names(node, role):
        if node is not None:
            for identifier in node.identifiers(): mark(identifier, role)

    def terminal(node):
        if node is None: return None
        if node.kind == 'identifier': return node
        if node.kind == 'generic_name': return next((n for n in node.children if n.kind == 'identifier'), None)
        return terminal(node.fields.get('name'))

    def declaration_kind(node):
        if node.kind in TYPES: return 'type'
        if node.kind in METHODS: return METHODS[node.kind]
        if node.kind in {'property_declaration', 'event_declaration'}: return 'property'
        if node.kind == 'enum_member_declaration': return 'enum-member'
        return None

    def precollect(node):
        for child in node.children:
            role = declaration_kind(child)
            if role: bind(child.fields.get('name'), role)
            elif child.kind in {'field_declaration', 'event_field_declaration'}:
                for value in child.descendants():
                    if value.kind == 'variable_declarator': bind(value.fields.get('name'), 'property')
            elif child.kind in {'declaration_list', 'global_statement'}: precollect(child)

    def visit(node):
        scoped = node.kind in SCOPE_KINDS
        if scoped:
            scopes.append({}); precollect(node)
            if node.kind == 'accessor_declaration': scopes[-1]['value'] = 'parameter'
        name = node.fields.get('name')
        role = declaration_kind(node)
        if role: bind(name, role)
        if node.kind in TYPES:
            type_role = 'type' if node.kind == 'record_declaration' and any(c.kind == 'struct' for c in node.children) else TYPES[node.kind]
            mark(name, type_role, True)
            if node.kind == 'record_declaration': features.add('records')
            if node.kind == 'enum_declaration': features.add('enums')
        elif node.kind in METHODS: mark(name, METHODS[node.kind], True); features.add('methods')
        elif node.kind in {'property_declaration', 'event_declaration'}:
            mark(name, 'property', True); features.add('properties')
        elif node.kind == 'enum_member_declaration': mark(name, 'enum-member', True)
        elif node.kind == 'type_parameter': bind(name, 'type'); mark(name, 'type', True); features.add('generics')
        elif node.kind == 'parameter':
            owner = node.parent.parent if node.parent else None
            record = owner is not None and owner.kind == 'record_declaration'
            bind(name, 'property' if record else 'parameter'); mark(name, 'property' if record else 'parameter', True)
        elif node.kind == 'implicit_parameter': bind(node, 'parameter'); mark(node, 'parameter', True)
        elif node.kind == 'variable_declarator':
            owner = node.parent.parent if node.parent else None
            field = owner is not None and owner.kind in {'field_declaration', 'event_field_declaration'}
            bind(name, 'property' if field else 'variable'); mark(name, 'property' if field else 'variable', True)
        elif node.kind == 'foreach_statement':
            value = node.fields.get('left')
            if value is not None:
                for identifier in value.identifiers(): bind(identifier, 'variable'); mark(identifier, 'variable', True)
        elif node.kind in {'declaration_expression', 'declaration_pattern', 'var_pattern', 'recursive_pattern', 'tuple_pattern'}:
            bind(name, 'variable'); mark(name, 'variable', True)
            if node.kind in {'declaration_pattern', 'var_pattern', 'recursive_pattern'}: features.add('patterns')
        elif node.kind == 'catch_declaration': bind(name, 'parameter'); mark(name, 'parameter', True)
        elif node.kind in {'from_clause', 'let_clause', 'join_clause', 'join_into_clause', 'query_continuation'}:
            value = name or next((c for c in node.children if c.kind == 'identifier'), None)
            bind(value, 'variable'); mark(value, 'variable', True); features.add('linq')
        elif node.kind == 'identifier' and node.start not in roles: mark(node, resolve(node.text))

        for child in node.children: visit(child)

        if node.kind in TYPE_CONTEXTS:
            for field in ('type', 'returns'):
                type_names(node.fields.get(field))
            if node.kind == 'as_expression': type_names(node.fields.get('right'))
        if node.kind in {'type_argument_list', 'base_list', 'type_parameter_constraints_clause', 'explicit_interface_specifier'}:
            type_names(node)
            if node.kind == 'type_argument_list': features.add('generics')
        if node.kind in {'namespace_declaration', 'file_scoped_namespace_declaration'}: names(name, 'namespace')
        if node.kind == 'using_directive':
            names(node, 'namespace'); features.add('imports')
        if node.kind == 'attribute': names(name, 'decorator'); features.add('attributes')
        if node.kind == 'member_access_expression':
            value = terminal(name)
            if value: mark(value, 'property')
        if node.kind == 'member_binding_expression':
            value = next((x for x in node.children if x.kind in {'identifier', 'generic_name'}), None)
            if terminal(value): mark(terminal(value), 'property')
        if node.kind == 'invocation_expression':
            value = terminal(node.fields.get('function'))
            if value is None:
                target = node.fields.get('function')
                if target is not None and target.kind == 'conditional_access_expression':
                    value = next((x for x in reversed(list(target.descendants())) if x.kind == 'identifier'), None)
            if value: mark(value, 'function' if resolve(value.text) == 'function' else 'method')
        if node.kind == 'object_creation_expression':
            value = terminal(node.fields.get('type'))
            if value: mark(value, 'constructor')
        if node.kind == 'argument' and name is not None: mark(name, 'parameter')
        if node.kind == 'tuple_element': mark(name, 'property')
        if node.kind == 'lambda_expression': features.add('lambdas')
        if node.kind in {'switch_expression', 'is_pattern_expression'}: features.add('patterns')
        if node.kind.startswith('preproc_'): features.add('directives')
        if node.kind == 'raw_string_literal': features.add('raw-strings')
        if node.kind == 'interpolated_string_expression':
            features.add('interpolated-strings')
            if '"""' in node.text: features.add('raw-strings')
        if node.kind == 'await_expression': features.add('async')
        if node.kind == 'collection_expression': features.add('collection-expressions')
        if scoped: scopes.pop()

    visit(tree)
    mapping, byte, units = {0: 0}, 0, 0
    for char in source:
        byte += len(char.encode('utf-8')); units += 2 if ord(char) > 0xffff else 1; mapping[byte] = units
    spans = ([{'start': 0, 'end': 1, 'tokenType': 'punctuation'}] if source.startswith('\ufeff') else [])
    for node in tree.descendants():
        if node.children or node.end == node.start: continue
        text = node.text
        if not text.strip(): continue
        if node.start not in mapping or node.end not in mapping: raise ValueError('Parser split an original Unicode character')
        modifiers = []
        if node.start in roles:
            role, declaration = roles[node.start]
            if declaration: modifiers = ['declaration']
        elif node.kind in STRINGS: role = 'string'
        elif node.kind in {'comment', 'shebang_directive'}: role = 'comment'; features.add('comments')
        elif node.kind in {'integer_literal', 'real_literal'}: role = 'number'
        elif node.kind in KEYWORD_NODES or text.startswith('#') or not node.named and text.isidentifier(): role = 'keyword'
        elif text in PUNCTUATION: role = 'punctuation'
        elif not node.named: role = 'operator'
        elif node.kind == 'identifier': role = 'variable'
        else: raise ValueError('Unmapped C# lexical node: ' + node.kind)
        span = {'start': mapping[node.start], 'end': mapping[node.end], 'tokenType': role}
        if modifiers: span['modifiers'] = modifiers
        spans.append(span)
    if '\r\n' in source: features.add('crlf')
    if any(ord(c) > 127 for c in source): features.add('unicode')
    return {'offsetEncoding': 'utf-16', 'spans': sorted(spans, key=lambda x: x['start']), 'features': sorted(features)}
