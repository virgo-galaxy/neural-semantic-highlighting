"""Original-coordinate Here Document ranges for the offline Bash teacher only.

The upstream lexer accepts a delimiter substring anywhere in the body. Shell
requires an entire terminator line, quote removal, and optional tab stripping.
Keep bodies opaque (including expansions), like the pack's other whole strings.
No source is executed; none of this module participates in neural inference.
"""
from functools import lru_cache


@lru_cache(maxsize=1)
def shell_lexer():
    from training.shared.offline_tools import load_lexer
    load_lexer('bash')  # Select the pinned, isolated offline package first.
    from pygments.lexers.shell import BashLexer
    from pygments.token import Operator

    class DeclarationLexer(BashLexer):
        tokens = {**BashLexer.tokens, 'basic': [
            (r'<<-?', Operator) if rule[0].startswith(r'<<-?') else rule
            for rule in BashLexer.tokens['basic']
        ]}
    return DeclarationLexer(stripnl=False, stripall=False, ensurenl=False)


def delimiter(source, start):
    """Read one delimiter word, removing shell quotes without expansion."""
    pos = start
    while pos < len(source) and source[pos] in ' \t': pos += 1
    value, quote, present = '', None, False
    while pos < len(source):
        char = source[pos]
        if quote:
            if char == quote: quote = None
            elif char == '\\' and quote == '"' and pos + 1 < len(source) and source[pos + 1] in '$`"\\':
                pos += 1; value += source[pos]
            else: value += char
        elif char in "'\"": quote = char; present = True
        elif char == '\\' and pos + 1 < len(source):
            pos += 1; value += source[pos]; present = True
        elif char.isspace() or char in ';&|<>()': break
        else: value += char; present = True
        pos += 1
    if quote or not present: raise ValueError('Unsupported or incomplete Here Document delimiter')
    return value, pos


def tokens(source):
    from pygments.token import Token as T
    parser = shell_lexer()
    masked, regions, body_cursors = source, [], {}
    # Rescan after masking each body so literal quotes, comments and redirections
    # inside it cannot change recognition of subsequent declarations.
    for _ in range(128):
        candidate = None; arithmetic = 0; previous = None
        for a, kind, text in parser.get_tokens_unprocessed(masked):
            if text == '$((': arithmetic += 1
            elif text == '(' and masked[a:a+2] == '((': arithmetic += 1
            elif text == '))': arithmetic = max(0, arithmetic - 1)
            elif text == ')' and previous == ')': arithmetic = max(0, arithmetic - 1)
            elif text in {'<<', '<<-'} and kind in T.Operator and not arithmetic:
                candidate = a, text; break
            previous = text
        if candidate is None: break
        start, operator = candidate
        word, end = delimiter(source, start + len(operator))
        newline = source.find('\n', end)
        if newline < 0: raise ValueError('Here Document has no body line')
        body_start = body_cursors.get(newline, newline + 1)
        pos = body_start
        while pos < len(source):
            line_end = source.find('\n', pos)
            if line_end < 0: line_end = len(source)
            content_end = line_end - (line_end > pos and source[line_end-1] == '\r')
            line = source[pos:content_end]
            if (line.lstrip('\t') if operator == '<<-' else line) == word:
                break
            pos = line_end + 1
        else: raise ValueError('Unterminated Here Document')
        body_cursors[newline] = min(len(source), line_end + 1)
        # Preserve the existing canonical contiguous-string representation when
        # no command syntax intervenes between the introducer and its body.
        if body_start == newline + 1 and not source[end:newline].strip():
            additions = [(start, content_end)]
        else:
            additions = [(start, end), (body_start, content_end)]
        for lo, hi in additions:
            regions.append((lo, hi))
            masked = masked[:lo] + ''.join(c if c in '\r\n' else ' ' for c in masked[lo:hi]) + masked[hi:]
    else: raise ValueError('Too many Here Documents in one source')
    regions.sort()
    # Masked whitespace can span several opaque regions. Split it at original
    # boundaries, preserving every original character and UTF-16 conversion.
    cuts = sorted({edge for region in regions for edge in region})
    result = []
    for a, kind, text in parser.get_tokens_unprocessed(masked):
        b = a + len(text)
        edges = [a] + [edge for edge in cuts if a < edge < b] + [b]
        for lo, hi in zip(edges, edges[1:]):
            role = T.String.Heredoc if any(x <= lo < y for x, y in regions) else kind
            value = source[lo:hi]
            if result and role == T.String.Heredoc and result[-1][1] == role and result[-1][0] + len(result[-1][2]) == lo:
                offset, _, old = result.pop(); result.append((offset, role, old + value))
            else: result.append((lo, role, value))
    return result
