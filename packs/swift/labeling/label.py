"""Official SwiftParser CST and bounded source-local roles; offline supervision only."""
from .parser import parse
from .tools import provenance

TYPES = {'structDecl':'type','classDecl':'type','actorDecl':'type','protocolDecl':'type','enumDecl':'enum','typeAliasDecl':'type','associatedTypeDecl':'type'}
OWNERS = set(TYPES) | {'extensionDecl','functionDecl','initializerDecl','deinitializerDecl','closureExpr','accessorDecl','sourceFile'}
SCOPES = OWNERS | {'codeBlock','forStmt','switchCase','catchClause','ifExpr'}
IDENTIFIERS = {'identifier','dollarIdentifier'}
STRINGS = {'stringQuote','multilineStringQuote','rawStringPoundDelimiter','stringSegment','singleQuote'}
PUNCTUATION = {'atSign','backslash','backtick','colon','colonColon','comma','leftAngle','rightAngle','leftBrace','rightBrace','leftParen','rightParen','leftSquare','rightSquare','period','semicolon','pound','ellipsis'}
OPERATORS = {'arrow','binaryOperator','equal','exclamationMark','infixQuestionMark','postfixOperator','postfixQuestionMark','prefixAmpersand','prefixOperator'}

def label(*, source, document_kind='swift', profile='swift'):
    if document_kind != 'swift' or profile != 'swift' or '\0' in source:
        raise ValueError('Expected original Swift source')
    tree, comments = parse(source)
    roles = {}; scopes = []; features = set()
    def tokens(n): return [] if n is None else [x for x in n.descendants() if x.kind == 'token' and x.end > x.start]
    def names(n): return [x for x in tokens(n) if x.token_kind in IDENTIFIERS]
    def first(n): return next(iter(names(n)), None)
    def ancestor(n, kinds):
        n = n.parent
        while n is not None:
            if n.kind in kinds: return n
            n = n.parent
        return None
    def mark(n, role, declaration=False):
        if n is not None:
            if n.kind != 'token': raise ValueError('Swift role requires an original token')
            roles[n.start] = (role, declaration)
    def key(n): return n.text.strip('`')
    def bind(n, role):
        if n is not None and key(n) != '_': scopes[-1][key(n)] = role
    def resolve(n):
        for scope in reversed(scopes):
            if key(n) in scope: return scope[key(n)]
        return 'variable'
    def declaration_role(n):
        owner = ancestor(n, OWNERS)
        return 'method' if owner is not None and owner.kind in set(TYPES) | {'extensionDecl'} else 'function'
    def variable_role(n):
        owner = ancestor(n, OWNERS)
        return 'property' if owner is not None and owner.kind in set(TYPES) | {'extensionDecl'} else 'variable'
    def pattern_names(n):
        return [x.fields['name'] for x in n.descendants() if x.kind == 'identifierPattern' and 'name' in x.fields] if n else []
    def precollect(n):
        for c in n.children:
            if c.kind in TYPES: bind(c.fields.get('name'), TYPES[c.kind])
            elif c.kind == 'functionDecl': bind(c.fields.get('name'), declaration_role(c))
            elif c.kind == 'genericParameter': bind(c.fields.get('name'), 'type-parameter')
            elif c.kind == 'enumCaseElement': bind(c.fields.get('name'), 'enum-member')
            elif c.kind == 'variableDecl':
                for binding in c.fields.get('bindings', c).children:
                    for name in pattern_names(binding.fields.get('pattern')): bind(name, variable_role(c))
            elif c.kind in {'codeBlockItemList','codeBlockItem','memberBlock','memberBlockItemList','memberBlockItem','enumCaseDecl','enumCaseElementList','genericParameterClause','genericParameterList'}:
                precollect(c)
    def type_names(n):
        for item in names(n):
            # Function-type labels are parameters, not type references.
            if item.field_name in {'firstName','secondName'}: continue
            r = resolve(item)
            mark(item, r if r in {'enum','type-parameter'} else 'type')
    def callee(n):
        if n is None: return None
        if n.kind == 'declReferenceExpr': return n.fields.get('name')
        if n.kind == 'memberAccessExpr': return callee(n.fields.get('member'))
        if n.kind in {'genericSpecializationExpr','optionalChainingExpr','forceUnwrapExpr','tryExpr','awaitExpr'}:
            return next((callee(c) for c in n.children if c.kind.endswith('Expr')), None)
        return None
    def visit(n):
        scoped = n.kind in SCOPES
        if scoped:
            scopes.append({}); precollect(n)
            if n.kind == "accessorDecl" and not n.fields.get("parameters"):
                accessor = n.fields.get("name")
                if accessor is not None and accessor.text in {"set","willSet","didSet"}:
                    scopes[-1]["oldValue" if accessor.text == "didSet" else "newValue"] = "parameter"
            if n.kind == "catchClause" and not any(c.kind == "identifierPattern" for c in n.descendants()): scopes[-1]["error"] = "parameter"
        name = n.fields.get('name')
        if n.kind in TYPES:
            mark(name, TYPES[n.kind], True); bind(name, TYPES[n.kind]); features.add('types')
        elif n.kind == 'functionDecl':
            mark(name, declaration_role(n), True); bind(name, declaration_role(n)); features.add('functions')
        elif n.kind in {'initializerDecl','deinitializerDecl'}:
            mark(name, 'constructor' if n.kind == 'initializerDecl' else 'method', True); features.add('initializers')
        elif n.kind == 'genericParameter':
            mark(name, 'type-parameter', True); bind(name, 'type-parameter'); features.add('generics')
        elif n.kind == 'enumCaseElement':
            mark(name, 'enum-member', True); bind(name, 'enum-member'); features.add('enums')
        elif n.kind in {'functionParameter','closureParameter'}:
            one, two = n.fields.get('firstName'), n.fields.get('secondName')
            if one is not None: mark(one, 'keyword' if one.text == '_' else 'parameter', two is None and one.text != '_')
            if two is not None: mark(two, 'keyword' if two.text == '_' else 'parameter', two.text != '_')
            bind(two or one, 'parameter')
        elif n.kind in {'tupleTypeElement','enumCaseParameter'}:
            for field in ['firstName','secondName']:
                item = n.fields.get(field)
                if item is not None: mark(item, 'keyword' if item.text == '_' else 'parameter')
        elif n.kind == 'macroDecl': mark(name, 'decorator', True); features.add('macros')
        elif n.kind == 'closureShorthandParameter': mark(name, 'parameter', True); bind(name, 'parameter')
        elif n.kind == 'accessorParameters': mark(name, 'parameter', True); bind(name, 'parameter')
        elif n.kind == 'identifierPattern':
            variable = ancestor(n, {'variableDecl','optionalBindingCondition','forStmt','catchClause','matchingPatternCondition','switchCase','closureExpr'})
            role = variable_role(variable) if variable is not None and variable.kind == 'variableDecl' else 'parameter' if variable is not None and variable.kind == 'catchClause' else 'variable'
            mark(name, role, True); bind(name, role); features.add('bindings')
        elif n.kind == 'closureCapture':
            mark(name, 'variable', True); bind(name, 'variable')
        elif n.kind == 'importPathComponent': mark(name, 'namespace'); bind(name, 'namespace'); features.add('imports')
        elif n.kind in {'labeledStmt','breakStmt','continueStmt'}: mark(name, 'label', n.kind == 'labeledStmt')
        elif n.kind == 'token' and n.token_kind in IDENTIFIERS and n.start not in roles:
            mark(n, 'parameter' if n.token_kind == 'dollarIdentifier' else resolve(n))
        for child in n.children: visit(child)
        if n.is_type: type_names(n)
        if n.kind == 'memberAccessExpr':
            item = callee(n); base = first(n.fields.get('base'))
            mark(item, 'constructor' if item is not None and item.text == 'init' else 'enum-member' if base is not None and resolve(base) == 'enum' else 'property')
        elif n.kind == 'functionCallExpr':
            target = n.fields.get('function'); item = callee(target)
            if item is not None:
                r = resolve(item)
                if r in {'type','enum'} or item.text == 'init': mark(item, 'constructor')
                elif target.kind == 'memberAccessExpr': mark(item, 'method')
                elif r in {'function','method'} or not any(key(item) in s for s in scopes): mark(item, 'function')
        elif n.kind == 'labeledExpr':
            item = n.fields.get('label')
            role = 'property' if ancestor(n, {'tupleExpr','functionCallExpr'}) is not None and ancestor(n, {'tupleExpr','functionCallExpr'}).kind == 'tupleExpr' else 'parameter'
            mark(item, role)
        elif n.kind == 'attribute':
            identifiers = names(n.fields.get('name'))
            for item in identifiers[:-1]: mark(item, 'namespace')
            if identifiers: mark(identifiers[-1], 'decorator')
            features.add('attributes')
        elif n.kind in {'macroExpansionExpr','macroExpansionDecl'}: mark(name, 'decorator'); features.add('macros')
        if n.kind == 'declNameArgument': mark(name, 'keyword' if name is not None and name.text == '_' else 'parameter')
        if n.kind == 'closureExpr': features.add('closures')
        if n.kind in {'awaitExpr','actorDecl'} or n.kind == 'token' and n.text in {'async','await','isolated','nonisolated','sending'}: features.add('async')
        if n.kind in {'arrayExpr','dictionaryExpr'}: features.add('collections')
        if n.kind == 'expressionSegment': features.add('interpolation')
        if n.kind in {'optionalBindingCondition','matchingPatternCondition','switchExpr','switchCase'}: features.add('patterns')
        if scoped: scopes.pop()
    visit(tree)
    units = {0:0}; byte = unit = 0
    for char in source:
        byte += len(char.encode()); unit += len(char.encode('utf-16-le')) // 2; units[byte] = unit
    spans = []; opaque_literals = []
    def append(start, end, role, declaration=False):
        if start == end: return
        if start not in units or end not in units: raise ValueError('Swift parser split an original Unicode character')
        value = dict(start=units[start], end=units[end], tokenType=role)
        if declaration: value['modifiers'] = ['declaration']
        spans.append(value)
    def atoms(n):
        if n.kind == 'regexLiteralExpr' or n.kind == 'stringLiteralExpr' and not any(x.kind == 'expressionSegment' for x in n.descendants()):
            features.add('strings'); opaque_literals.append((n.start,n.end)); append(n.start, n.end, 'string'); return
        if n.kind != 'token':
            for c in n.children: atoms(c)
            return
        if n.end <= n.start or n.token_kind == 'endOfFile': return
        text = n.text; decl = False
        if n.start in roles: role, decl = roles[n.start]
        elif n.token_kind in STRINGS:
            role = 'punctuation' if ancestor(n, {'expressionSegment'}) else 'string'; features.add('strings')
        elif n.token_kind in {'integerLiteral','floatLiteral'}: role = 'number'
        elif n.token_kind in {'keyword','wildcard'} or n.token_kind.startswith('pound') and n.token_kind != 'pound': role = 'keyword'
        elif n.token_kind == 'shebang': role = 'comment'
        elif n.token_kind in PUNCTUATION: role = 'punctuation'
        elif n.token_kind in OPERATORS: role = 'operator'
        else: raise ValueError('Unmapped original Swift lexical token: ' + n.token_kind)
        append(n.start, n.end, role, decl)
    atoms(tree)
    for comment in comments:
        start, end = comment['start'], comment['end']
        text = source.encode()[start:end].decode(); end -= len(text) - len(text.rstrip('\r\n'))
        role = comment['kind']
        if role == 'string' and any(lo <= start and end <= hi for lo,hi in opaque_literals): continue
        append(start, end, role); features.add('comments' if role == 'comment' else 'strings')
    if source.startswith('\ufeff'): append(0, 3, 'punctuation')
    spans.sort(key=lambda s:s['start'])
    merged = []; end = 0; raw = source.encode('utf-16-le')
    for span in spans:
        if span['start'] < end or raw[end*2:span['start']*2].decode('utf-16-le').strip():
            raise ValueError(f'Incomplete or overlapping original Swift Gold: previous end={end}, span={span}, context={raw[max(0,end-20)*2:(span["end"]+20)*2].decode("utf-16-le",errors="replace")!r}')
        if merged and span['tokenType'] == 'string' and merged[-1]['tokenType'] == 'string' and merged[-1]['end'] == span['start']:
            merged[-1]['end'] = span['end']
        else: merged.append(span)
        end = span['end']
    if raw[end*2:].decode('utf-16-le').strip(): raise ValueError('Unmapped original Swift source suffix')
    if '\r\n' in source: features.add('crlf')
    if any(ord(c) > 127 for c in source): features.add('unicode')
    return dict(offsetEncoding='utf-16', spans=merged, features=sorted(features))
