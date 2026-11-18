"""Offline original-coordinate GNU Make source roles; never invoke make or expand code."""
from __future__ import annotations
import re
from .parser import parser
from .tools import provenance as parser_provenance
from packs.bash.labeling.label import label as shell_label
from training.shared.offline_tools import provenance as shell_provenance

REFERENCES = {'variable_reference', 'automatic_variable', 'substitution_reference'}
EXPANSIONS = REFERENCES | {'function_call', 'shell_function'}
NUMBER = re.compile(r'[+-]?(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d+)?)\Z')


def provenance():
    return dict(structure=parser_provenance(), shell=shell_provenance(),
                sourceExecution=False, includesLoaded=False, expansionsEvaluated=False)


def label(*, source, document_kind='makefile', profile='makefile'):
    if not isinstance(source, str) or document_kind != 'makefile' or profile != 'makefile':
        raise ValueError('Expected original Makefile source and matching profile')
    if any(ord(c) < 32 and c not in '\t\r\n' for c in source) or '\x7f' in source or '\r' in source.replace('\r\n', ''):
        raise ValueError('Unsupported Makefile control or bare CR')
    source.encode('utf-8')
    # The CST requires a final newline. This parse-only sentinel never enters Gold.
    bom = source.startswith('\ufeff')
    projection = list(source[1:] if bom else source)
    prefix = '\t'
    cursor = 0; conditional_depth = 0; defining = False; opaque_ranges = []
    continuing_make = continuing_recipe = False
    # Only literal, unconditional one-byte .RECIPEPREFIX assignments can be mapped.
    # Keep a checked original coordinate for every character; no source is expanded.
    for line in ''.join(projection).splitlines(keepends=True):
        recipe_line = continuing_recipe or (line.startswith(prefix) and not continuing_make)
        if not recipe_line and not continuing_make:
            directive = re.match(r'[ ]*(override[ ]+)?(define|endef|ifeq|ifneq|ifdef|ifndef|endif)\b', line)
            if directive:
                name = directive[2]
                if name == 'define': defining = True
                elif name == 'endef': defining = False
                elif not defining and name == 'endif': conditional_depth -= 1
                elif not defining: conditional_depth += 1
        if defining:
            opaque_ranges.append((cursor + int(bom), cursor + len(line) + int(bom)))
            cursor += len(line); continue
        match = re.fullmatch(r'[ \t]*\.RECIPEPREFIX[ \t]*(?::=|=)[ \t]*([^\r\n$#]*)\r?\n?', line)
        if match:
            if conditional_depth: raise ValueError('Conditional recipe prefix is outside the source-local contract')
            value = match[1].strip()
            if len(value) > 1 or (value and (not value.isascii() or value.isspace())):
                raise ValueError('Unsupported computed recipe prefix')
            prefix = value or '\t'
            if not value:
                # The pinned grammar requires a nonempty special-prefix value.
                # A same-character-count name projection selects its ordinary
                # empty-assignment production; original output still names it.
                projection[cursor + line.index('.RECIPEPREFIX')] = '_'
        elif recipe_line and prefix != '\t' and line.startswith(prefix):
            projection[cursor] = '\t'
        if recipe_line: opaque_ranges.append((cursor + int(bom), cursor + len(line) + int(bom)))
        content=line.rstrip('\r\n'); slash_count=len(content)-len(content.rstrip('\\'))
        continuing_make=bool(slash_count%2) and not recipe_line
        continuing_recipe=bool(slash_count%2) and recipe_line
        cursor += len(line)
    comments = []; stack = []; cursor = int(bom); index = 0
    while cursor < len(source):
        while index < len(opaque_ranges) and opaque_ranges[index][1] <= cursor: index += 1
        if index < len(opaque_ranges) and opaque_ranges[index][0] <= cursor:
            cursor = opaque_ranges[index][1]; stack = []; continue
        char = source[cursor]
        if char == '\\' and cursor+1 < len(source): cursor += 2; continue
        if source.startswith('$$', cursor): cursor += 2; continue
        if char == '$' and cursor+1 < len(source) and source[cursor+1] in '({':
            stack.append(')' if source[cursor+1] == '(' else '}'); cursor += 2; continue
        if stack:
            if char == stack[-1]: stack.pop()
            elif char in '({': stack.append(')' if char == '(' else '}')
        elif char == '#':
            start = cursor
            while True:
                stop = source.find('\n',cursor)
                if stop < 0: stop = len(source)
                end = stop-1 if stop and source[stop-1:stop] == '\r' else stop
                tail = end
                while tail > start and source[tail-1] == '\\': tail -= 1
                if (end-tail)%2 and stop < len(source): cursor=stop+1; continue
                break
            comments.append((start,end))
            for i in range(start,end):
                if source[i] not in '\r\n': projection[i-int(bom)] = ' '
            cursor = stop; continue
        cursor += 1
    projected = ''.join(projection)
    raw = projected.encode('utf-8')
    if raw and not raw.endswith(b'\n'): raw += b'\n'
    tree = parser().parse(raw)
    byte_to_char = {0: int(bom)}
    byte = 0
    for index, char in enumerate(projected):
        byte += len(char.encode('utf-8')); byte_to_char[byte] = index + 1 + int(bom)
    byte_to_char[len(raw)] = len(source)
    units = [0]
    for char in source: units.append(units[-1] + len(char.encode('utf-16-le')) // 2)
    spans = []; features = set()

    def bounds(node):
        return byte_to_char[node.start], byte_to_char[node.end]

    def adjacent_assignment(node):
        name, operator = node.fields.get('name'), node.fields.get('operator')
        if name is None or operator is None or node.kind != 'variable_assignment': return False
        a,b = bounds(name); left,right = bounds(operator)
        return b == left and source[left:right] == '=' and source[a:b].endswith(('?', '+')) and not source[a:b].endswith(('\\?', '\\+'))

    def add(a, b, role, mods=()):
        if a >= b: return
        span = dict(start=units[a], end=units[b], tokenType=role)
        if mods: span['modifiers'] = list(mods)
        spans.append(span)

    def literal(a, b, role='string', mods=(), commas=False):
        for left, right in comments:
            if left < b and a < right:
                literal(a,min(b,left),role,mods,commas) if a < left else None
                literal(max(a,right),b,role,mods,commas) if right < b else None
                return
        if commas:
            cursor = a
            for match in re.finditer(',', source[a:b]):
                at = a + match.start(); literal(cursor,at,role,mods); add(at,at+1,'punctuation'); cursor=at+1
            literal(cursor,b,role,mods); return
        for match in re.finditer(r'\\(?=\r?\n)|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\S+', source[a:b]):
            lo, hi = a + match.start(), a + match.end()
            if match[0] == '\\' and (source[hi:hi+2] == '\r\n' or source[hi:hi+1] == '\n'):
                add(lo,hi,'punctuation'); features.add('continuations')
            else: add(lo, hi, 'number' if role == 'string' and NUMBER.fullmatch(match[0]) else role, mods)

    foreign_shell = False
    for node in tree.descendants():
        if node.kind not in {'variable_assignment', 'shell_assignment'}: continue
        name, value = node.fields.get('name'), node.fields.get('value')
        if name is not None and name.text == 'SHELL':
            value_text = value.text.strip() if value is not None else ''
            if value_text.rsplit('/', 1)[-1] not in {'sh', 'bash', 'ash', 'dash', 'zsh'}:
                foreign_shell = True

    def shell(node, recipe=False):
        a, b = bounds(node)
        if recipe:
            features.add('recipes')
            while a < b and source[a] in ' \t': a += 1
            while a < b and source[a] in '@-+': add(a, a+1, 'operator'); a += 1
        if foreign_shell:
            if a < b: add(a, b, 'string')
            features.add('opaque-shell'); return
        masks = []
        def collect(child):
            lo, hi = bounds(child)
            if child.kind in EXPANSIONS and not source[lo:hi].startswith('$$'):
                masks.append((lo, hi, child)); return
            for nested in child.children: collect(nested)
        for child in node.children: collect(child)
        masks.sort()
        projected_chars = []; positions = [a]; cursor = a; index = 0
        while cursor < b:
            if index < len(masks) and cursor == masks[index][0]:
                end = masks[index][1]
                while cursor < end:
                    projected_chars.append(source[cursor] if source[cursor] in '\r\n' else 'x')
                    cursor += 1; positions.append(cursor)
                index += 1
            elif source.startswith('$$', cursor):
                projected_chars.append('$'); cursor += 2; positions.append(cursor)
            else:
                projected_chars.append(source[cursor]); cursor += 1; positions.append(cursor)
        child_source = ''.join(projected_chars)
        if child_source and not child_source.endswith('\n'):
            child_source += '\n'; positions.append(b)
        child_units = {0: 0}; total = 0
        for i, char in enumerate(child_source):
            total += len(char.encode('utf-16-le')) // 2; child_units[total] = i+1
        result = shell_label(source=child_source, profile='bash')
        for span in result['spans']:
            lo, hi = positions[child_units[span['start']]], positions[child_units[span['end']]]
            pieces = [(lo, hi)]
            for left, right, _ in masks:
                pieces = [(x, y) for x, y in ((x, min(y, left)) for x,y in pieces) if x < y] + [(max(x, right), y) for x,y in pieces if max(x, right) < y]
            for lo, hi in pieces: add(lo, hi, span['tokenType'], span.get('modifiers', ()))
        for _, _, child in masks: visit(child)

    def visit(node, role='string', mods=(), commas=False):
        a, b = bounds(node)
        if node.kind == 'arguments': commas = True
        if node.kind == 'comment':
            while b > a and source[b-1] in '\r\n': b -= 1
            add(a, b, 'comment'); features.add('comments'); return
        if node.kind in REFERENCES:
            escaped = source[a:b].startswith('$$')
            add(a, b, 'string' if escaped else 'variable')
            features.add('escaped-dollars' if escaped else 'variables'); return
        if node.kind == 'raw_text':
            add(a, b, 'string'); features.add('defines'); return
        if node.kind == 'recipe_line': shell(node, True); return
        if node.kind == 'shell_command': shell(node); return
        if node.kind in {'function_call', 'shell_function'}: features.add('functions')
        if node.kind == 'rule': features.add('rules')
        if node.kind == 'conditional': features.add('conditionals')
        if node.kind.endswith('_directive'): features.add('directives')
        if node.kind in {'targets', 'pattern_list'}: features.add('patterns' if '%' in source[a:b] else 'rules')
        if node.kind == 'targets' or getattr(node, 'field_name', '') == 'target_or_pattern':
            role, mods = 'label', ('declaration',)
        field = getattr(node, 'field_name', '')
        if field == 'name' and node.parent.kind in {'variable_assignment', 'shell_assignment', 'VPATH_assignment', 'RECIPEPREFIX_assignment', 'define_directive'}:
            add(a, b-1 if adjacent_assignment(node.parent) else b, 'variable', ('declaration',)); features.add('variables'); return
        if field == 'operator' and adjacent_assignment(node.parent):
            add(a-1,b,'operator'); return
        if field == 'function':
            add(a, b, 'function', ('default-library',)); return
        if field == 'variable' or (node.parent and node.parent.kind in {'export_directive', 'unexport_directive'} and node.kind == 'list'):
            role, mods = 'variable', ()
        if not node.children:
            if not node.named:
                if node.kind == '\t':
                    if a < b and source[a] != '\t': add(a, b, 'punctuation')
                elif node.kind in {'=', ':=', '::=', '+=', '?=', '!=', '$', '$$', '|'}: add(a,b,'operator')
                elif node.kind in {':', '::', '&:', ';', '(', ')', ',', '\\'}:
                    add(a,b,'punctuation')
                    if node.kind == '\\': features.add('continuations')
                elif node.kind in {'"', "'"}: add(a,b,'string')
                else: literal(a,b,'keyword')
            else: literal(a,b,role,mods,commas)
            return
        cursor = a
        for child in node.children:
            lo, hi = bounds(child)
            if lo < cursor or hi > b: raise ValueError('Make CST original range mismatch')
            literal(cursor,lo,role,mods,commas); visit(child,role,mods,commas); cursor = hi
        literal(cursor,b,role,mods,commas)

    if bom: add(0,1,'punctuation'); features.add('bom')
    visit(tree)
    for a,b in comments: add(a,b,'comment'); features.add('comments')
    spans.sort(key=lambda span:(span['start'],span['end']))
    merged=[]; cursor=0; raw16=source.encode('utf-16-le')
    for span in spans:
        if span['start'] < cursor: raise ValueError('Overlapping Makefile source spans')
        if raw16[cursor*2:span['start']*2].decode('utf-16-le').strip(): raise ValueError('Uncovered Makefile source')
        if merged and span['tokenType']=='string' and merged[-1]['tokenType']=='string' and merged[-1].get('modifiers')==span.get('modifiers') and merged[-1]['end']==span['start']:
            merged[-1]['end']=span['end']
        else: merged.append(span)
        cursor=span['end']
    if raw16[cursor*2:].decode('utf-16-le').strip(): raise ValueError('Uncovered Makefile suffix')
    if '\r\n' in source: features.add('crlf')
    if any(ord(c)>127 for c in source): features.add('unicode')
    return dict(offsetEncoding='utf-16',spans=merged,features=sorted(features))
