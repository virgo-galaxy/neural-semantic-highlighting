"""Offline source-local assembly display Gold; no assembler or input execution."""
from bisect import bisect_right
from functools import lru_cache
import re

from training.shared.offline_tools import load_lexer, provenance

PROFILES = {'nasm', 'gas', 'masm', 'aarch64'}
REGISTERS = re.compile(
    r'%?(?:r(?:1[0-5]|[8-9])(?:[bwd])?|[er]?(?:ax|bx|cx|dx|si|di|sp|bp|ip)|'
    r'[abcd][lh]|[cdefgs]s|(?:[xyz]mm)(?:[12]?[0-9]|3[01])|mm[0-7]|k[0-7]|'
    r'st(?:[0-7])?|[cd]r[0-9]+|bnd[0-3]|'
    r'[xw](?:[12]?[0-9]|30)|[vqdsbhz](?:[12]?[0-9]|3[01])(?:\.(?:[124816]+)?[bhsd])?|'
    r'p(?:1[0-5]|[0-9])(?:\.[bhsd])?|sp|wsp|xzr|wzr|lr|fp|ffr)', re.I)
ARM_CONTEXT = re.compile(r'(?<![%\w])(?:[xw](?:[12]?[0-9]|30)|sp|[vqdsbhz][0-9]+(?:\.[0-9]+[bhsd])?)\b', re.I)
TYPES = set('byte word dword qword tword oword yword zword ptr near far short long real4 real8 real10'.split())
DIRECTIVES = set('bits use16 use32 use64 default section segment ends global public extern extrn export import align alignb org cpu absolute struc endstruc common end proc endp frame macro endm equ textequ set db dw dd dq dt do dy dz resb resw resd resq rest reso resy resz times dup offset option include includelib assume invoke local model flat code data const title name if ifdef ifndef else elseif endif repeat while exitm'.split())
DATA = set('equ textequ set db dw dd dq dt do dy dz resb resw resd resq rest reso resy resz byte word dword qword real4 real8 real10'.split())
DIRECTIVES |= DATA
OPERATIONS = set('mov movzx movsx movsxd add sub adc sbb cmp test and or xor inc dec neg not push pop call jmp imul mul idiv div lea xchg cmpxchg xadd movdqu movdqa vmovdqu vmovdqa fld fst fstp fadd fsub fmul fdiv lock rep'.split())
PREFIXES = set('lock rep repe repz repne repnz data16 data32 addr16 addr32 rex rex64'.split())
ENTRY = {'cglobal', 'leaf_entry', 'nested_entry', 'alternate_entry'}
BRANCH = re.compile(r'(?:j\w+|call\w*|invoke|loop\w*|b(?:\.[a-z]+)?|bl|br|blr|cbz|cbnz|tbz|tbnz)', re.I)


@lru_cache(maxsize=1)
def lexer():
    load_lexer('nasm')
    from pygments.lexer import RegexLexer
    from pygments.token import Comment, String, Number, Name, Operator, Punctuation, Text, Keyword

    def hash_region(parser, match):
        prefix = match.string[match.string.rfind('\n', 0, match.start()) + 1:match.start()]
        command = prefix.strip().split(None, 1)[0].lower() if prefix.strip() else ''
        if ARM_CONTEXT.search(prefix) or command in {'svc', 'hvc', 'smc', 'brk', 'hint', 'dmb', 'dsb', 'isb'}:
            yield match.start(), Operator, '#'
            for offset, kind, text in parser.get_tokens_unprocessed(match.group()[1:]):
                yield match.start() + 1 + offset, kind, text
        else:
            yield match.start(), Comment.Single, match.group()

    class DisplayAssemblyLexer(RegexLexer):
        flags = re.MULTILINE | re.IGNORECASE
        tokens = {'root': [
            (r'^[ \t]*#[ \t]*(?:include|define|undef|if|ifdef|ifndef|elif|else|endif|pragma|error|line)\b', Keyword),
            (r'/\*[\s\S]*?\*/', Comment.Multiline),
            (r';[^\r\n]*|//[^\r\n]*', Comment.Single),
            (r'#[^\r\n]*', hash_region),
            (r'"(?:\\[\s\S]|[^"\\\r\n])*"|\'(?:\\[\s\S]|[^\'\\\r\n])*\'|`(?:\\[\s\S]|[^`\\\r\n])*`', String),
            (r'%%[\w.$?@]+|%\{?\d+\}?|\\[A-Za-z_][\w.]*', Name.Variable.Magic),
            (r'%[A-Za-z_][\w]*', Name),
            (r'\d+[fb]\b', Name.Label),
            (r'(?:0x[\da-f]+|0b[01]+|\d[\da-f]*h|\d+[boqd]|\d+(?:\.\d+)?(?:e[+-]?\d+)?)\b', Number),
            (r'[A-Za-z_.?@][\w.$?@]*', Name),
            (r'\s+', Text),
            (r'<<|>>|\$\$|##|[+*/%&|^~!=<>$-]', Operator),
            (r'[:,\[\](){}]', Punctuation),
            (r'[^\s]', Operator),
        ]}
    return DisplayAssemblyLexer(stripnl=False, stripall=False, ensurenl=False)


def label(*, source, document_kind='assembly', profile='nasm'):
    if document_kind != 'assembly' or profile not in PROFILES or '\0' in source:
        raise ValueError('Expected original assembly source and a declared coverage profile')
    parser = lexer()
    from pygments.token import Token as T
    tokens = []
    cursor = 0
    for start, kind, text in parser.get_tokens_unprocessed(source):
        if not text:
            continue
        if start != cursor or source[start:start + len(text)] != text:
            raise ValueError('Offline lexer changed original assembly coordinates')
        cursor = start + len(text)
        if kind in T.Error and text.strip():
            raise ValueError('Unsupported assembly token')
        if kind in T.String or kind in T.Comment:
            tokens.append((start, cursor, kind, text))
        else:
            lo, hi = len(text) - len(text.lstrip()), len(text.rstrip())
            if lo < hi:
                tokens.append((start + lo, start + hi, kind, text[lo:hi]))
    if cursor != len(source):
        raise ValueError('Uncovered assembly suffix')
    line_starts = [0] + [match.end() for match in re.finditer('\n', source)]
    lines = {}
    for index, (a, _, kind, _) in enumerate(tokens):
        if kind not in T.Comment:
            lines.setdefault(bisect_right(line_starts, a), []).append(index)
    definitions, commands, directive_commands = {}, set(), set()
    for indices in lines.values():
        j = 0
        while j + 1 < len(indices) and tokens[indices[j + 1]][3] == ':':
            definitions[indices[j]] = 'variable' if tokens[indices[j]][3].startswith('%%') else 'function'
            j += 2
        if j >= len(indices):
            continue
        first = tokens[indices[j]][3].lower()
        following = tokens[indices[j + 1]][3].lower() if j + 1 < len(indices) else ''
        if following in {'proc', 'macro', 'endp'} | DATA and first not in OPERATIONS:
            if following != 'endp':
                definitions[indices[j]] = 'function' if following in {'proc', 'macro'} else 'variable'
            j += 1
            first = following
        if first in ENTRY | {'.macro', '%macro', '%imacro'} and j + 1 < len(indices):
            definitions[indices[j + 1]] = 'function'
        elif first in {'.equ', '.equiv', '.set', '%define', '%xdefine', '%assign', '#define'} and j + 1 < len(indices):
            definitions[indices[j + 1]] = 'variable'
        while j < len(indices):
            index = indices[j]
            word = tokens[index][3].lower()
            commands.add(index)
            if word.startswith(('.', '%', '#')) or word in DIRECTIVES or word in ENTRY:
                directive_commands.add(index)
            if word not in PREFIXES:
                break
            j += 1
    labels = {tokens[i][3].lower() for i, role in definitions.items() if role == 'function'}
    units = [0]
    for char in source:
        units.append(units[-1] + (2 if ord(char) > 65535 else 1))
    output, features = [], {'profile:' + profile}
    for i, (a, b, kind, text) in enumerate(tokens):
        low, modifiers = text.lower(), []
        if kind in T.Comment:
            role = 'comment'
            features.add('comments')
        elif kind in T.String:
            role = 'string'
            features.add('strings')
        elif i in definitions:
            role, modifiers = definitions[i], ['declaration']
            features.add('labels' if role == 'function' else 'data')
        elif REGISTERS.fullmatch(text):
            role, modifiers = 'variable', ['default-library']
            features.add('registers')
        elif kind in T.Name.Variable.Magic:
            role = 'parameter' if not text.startswith('%%') else 'variable'
            features.add('macros')
        elif i in commands or kind in T.Keyword:
            role = 'keyword'
            features.add('directives' if i in directive_commands or kind in T.Keyword else 'instructions')
        elif low in {'rel', 'abs', 'strict', 'wrt', 'seg', 'offset'}:
            role = 'operator'
        elif low == 'frame':
            role = 'keyword'
        elif low in TYPES:
            role = 'type'
        elif kind in T.Number:
            role = 'number'
            features.add('numbers')
        elif kind in T.Name.Label:
            role = 'function' if low[:-1] in labels or low.endswith('f') else 'number'
        elif kind in T.Operator:
            role = 'operator'
        elif kind in T.Punctuation:
            role = 'punctuation'
            if text in {'[', '('}:
                features.add('memory')
        else:
            line = lines[bisect_right(line_starts, a)]
            command = next((tokens[x][3] for x in line if x in commands), '')
            role = 'function' if low in labels or BRANCH.fullmatch(command) else 'variable'
        span = {'start': units[a], 'end': units[b], 'tokenType': role}
        if modifiers:
            span['modifiers'] = modifiers
        if role == 'comment' and output and output[-1]['tokenType'] == role and output[-1]['end'] == span['start']:
            output[-1]['end'] = span['end']
        else:
            output.append(span)
    if '\r\n' in source:
        features.add('crlf')
    if any(ord(char) > 127 for char in source):
        features.add('unicode')
    return {'offsetEncoding': 'utf-16', 'spans': output, 'features': sorted(features)}
