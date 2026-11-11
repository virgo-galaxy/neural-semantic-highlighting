"""Official Kotlin PSI/lexer and bounded source-local roles; never used in inference."""
from .parser import parse
from .tools import provenance

TYPE_NODES={'KtClass','KtObjectDeclaration','KtTypeAlias'}
OWNERS=TYPE_NODES|{'KtEnumEntry','KtNamedFunction','KtSecondaryConstructor','KtFunctionLiteral','KtPropertyAccessor','KtFile','KtScript'}
SCOPES=OWNERS|{'KtBlockExpression','KtForExpression','KtCatchClause','KtWhenExpression','KtWhenEntry'}
PUNCTUATION={'LPAR','RPAR','LBRACE','RBRACE','LBRACKET','RBRACKET','DOT','COMMA','COLON','SEMICOLON','AT','HASH'}
STRING_PARTS={'OPEN_QUOTE','CLOSING_QUOTE','REGULAR_STRING_PART','ESCAPE_SEQUENCE','CHARACTER_LITERAL','INTERPOLATION_PREFIX'}
EXTRA_OPERATORS={'ARROW','QUEST','EXCLEXCL','COLONCOLON','SAFE_ACCESS','ELVIS'}
INTERPOLATION={'SHORT_TEMPLATE_ENTRY_START','LONG_TEMPLATE_ENTRY_START','LONG_TEMPLATE_ENTRY_END'}


def label(*,source,document_kind='kotlin',profile='kotlin'):
    if document_kind!='kotlin' or profile not in {'kotlin','kotlin-script'} or '\0' in source:
        raise ValueError('Expected original Kotlin source/script')
    tree,tokens=parse(source,script=profile=='kotlin-script');raw=source.encode('utf-16-le')
    lexical={t['start']:t for t in tokens};roles={};scopes=[];features=set()
    def text(start,end):return raw[start*2:end*2].decode('utf-16-le')
    def ancestor(n,kinds):
        n=n.parent
        while n is not None:
            if n.kind in kinds:return n
            n=n.parent
        return None
    def leaf(n):
        if n is None:return None
        if not n.children:return n
        return next((x for x in n.descendants() if not x.children and x.syntax_type=='IDENTIFIER'),None)
    def names(n):
        return [] if n is None else [x for x in n.descendants() if x.kind=='KtNameReferenceExpression' and x.fields.get('name')]
    def reference(n):return None if n is None else n.fields.get('name')
    def key(n):return n.text.strip('`')
    def mark(n,role,decl=False):
        if n is not None and n.end>n.start:
            if n.start not in lexical or lexical[n.start]['end']!=n.end:
                raise ValueError('Kotlin role is not one complete original lexer token: '+n.kind)
            roles[n.start]=(role,decl)
    def bind(n,role):
        if n is not None and n.text!='_':scopes[-1][key(n)]=role
    def resolve(n):
        for scope in reversed(scopes):
            if key(n) in scope:return scope[key(n)]
        return 'variable'
    def type_role(n):return 'enum' if n.meta.get('enum') else 'type'
    def function_role(n):
        p=n.parent
        while p is not None:
            if p.kind in {'KtBlockExpression','KtNamedFunction','KtSecondaryConstructor','KtFunctionLiteral','KtPropertyAccessor'}:return 'function'
            if p.kind in TYPE_NODES|{'KtEnumEntry'}:return 'method'
            p=p.parent
        return 'function'
    def property_role(n):
        if n.meta.get('constant'):return 'constant'
        p=n.parent
        while p is not None:
            if p.kind in SCOPES-TYPE_NODES-{'KtEnumEntry','KtFile'}:return 'variable'
            if p.kind in TYPE_NODES|{'KtEnumEntry'}:return 'property'
            p=p.parent
        return 'variable'
    def parameter_role(n):
        if n.meta.get('propertyParameter'):return 'property'
        owner=ancestor(n,{'KtForExpression','KtCatchClause','KtNamedFunction','KtPrimaryConstructor','KtSecondaryConstructor','KtFunctionLiteral','KtFunctionType'})
        return 'variable' if owner is not None and owner.kind=='KtForExpression' else 'parameter'
    def precollect(n):
        for c in n.children:
            name=c.fields.get('name')
            if c.kind in TYPE_NODES:bind(name,type_role(c))
            elif c.kind=='KtEnumEntry':bind(name,'enum-member')
            elif c.kind=='KtNamedFunction':bind(name,function_role(c))
            elif c.kind=='KtProperty':bind(name,property_role(c))
            elif c.kind=='KtTypeParameter':bind(name,'type-parameter')
            elif c.kind=='KtParameter':bind(name,parameter_role(c))
            elif c.kind in {'KtClassBody','KtParameterList','KtPrimaryConstructor','KtTypeParameterList','KtScriptInitializer'}:precollect(c)
    def type_names(n):
        if n is None or n.kind=='KtAnnotationEntry':return
        if n.kind=='KtNameReferenceExpression':
            name=n.fields.get('name')
            if name is not None:
                r=resolve(name);mark(name,r if r in {'enum','type-parameter'} else 'type')
            return
        for c in n.children:type_names(c)
    def callee(n):
        if n is None:return None
        if n.kind=='KtNameReferenceExpression':return n.fields.get('name')
        if n.kind=='KtConstructorCalleeExpression':
            refs=names(n.fields.get('type'));return reference(refs[-1]) if refs else None
        if n.kind in {'KtDotQualifiedExpression','KtSafeQualifiedExpression'}:return callee(n.fields.get('selector'))
        if n.kind=='KtCallExpression':return callee(n.fields.get('function'))
        if n.kind in {'KtParenthesizedExpression','KtPostfixExpression'}:
            return next((callee(c) for c in n.children if c.kind.startswith('Kt')),None)
        return None
    enum_names={key(n.fields['name']):{key(c.fields['name']) for c in n.descendants() if c.kind=='KtEnumEntry' and c.fields.get('name')} for n in tree.descendants() if n.kind=='KtClass' and n.meta.get('enum') and n.fields.get('name')}
    def mask_constructor_parameters(n):
        owner=ancestor(n,OWNERS)
        if owner is None or owner.kind not in TYPE_NODES:return
        constructor=next((c for c in owner.children if c.kind=='KtPrimaryConstructor'),None)
        if constructor:
            for p in constructor.descendants():
                if p.kind=='KtParameter' and not p.meta.get('propertyParameter') and p.fields.get('name'):
                    scopes[-1][key(p.fields['name'])]='variable'
    def visit(n):
        scoped=n.kind in SCOPES
        if scoped:
            scopes.append({})
            if n.kind=='KtPropertyAccessor' or n.kind=='KtNamedFunction' and function_role(n)=='method':mask_constructor_parameters(n)
            if n.kind=='KtFunctionLiteral' and not n.meta.get('explicitParameters'):scopes[-1]['it']='parameter'
            if n.kind=='KtPropertyAccessor':
                scopes[-1]['field']='property'
                if n.meta.get('accessor')=='set':scopes[-1]['value']='parameter'
            precollect(n)
        name=n.fields.get('name')
        if n.kind in TYPE_NODES:mark(name,type_role(n),True);bind(name,type_role(n));features.add('types')
        elif n.kind=='KtEnumEntry':mark(name,'enum-member',True);bind(name,'enum-member');features.add('enums')
        elif n.kind=='KtNamedFunction':mark(name,function_role(n),True);bind(name,function_role(n));features.add('functions')
        elif n.kind=='KtSecondaryConstructor':mark(name,'constructor',True);features.add('constructors')
        elif n.kind=='KtTypeParameter':mark(name,'type-parameter',True);bind(name,'type-parameter');features.add('generics')
        elif n.kind=='KtProperty':mark(name,property_role(n),True);bind(name,property_role(n));features.add('properties')
        elif n.kind=='KtParameter':
            owner=ancestor(n,{'KtFunctionType','KtNamedFunction','KtPrimaryConstructor','KtSecondaryConstructor','KtFunctionLiteral','KtForExpression','KtCatchClause','KtPropertyAccessor'})
            is_type=owner is not None and owner.kind=='KtFunctionType'
            mark(name,'keyword' if name is not None and name.text=='_' else parameter_role(n),not is_type and (name is None or name.text!='_'))
            if not is_type:bind(name,parameter_role(n))
            if n.meta.get('propertyParameter'):features.add('properties')
        elif n.kind=='KtDestructuringDeclarationEntry':
            p=ancestor(n,{'KtParameter'});role=parameter_role(p) if p else 'variable'
            mark(name,'keyword' if name is not None and name.text=='_' else role,name is None or name.text!='_');bind(name,role);features.add('destructuring')
        elif n.kind=='KtNameReferenceExpression' and name is not None and name.start not in roles:mark(name,resolve(name))
        elif n.kind=='KtLabelReferenceExpression':mark(name or leaf(n),'label')
        for c in n.children:visit(c)
        if n.meta.get('isType'):type_names(n)
        if n.kind in {'KtTypeParameterList','KtTypeArgumentList'}:
            for c in n.children:
                if not c.children and c.syntax_type in {'LT','GT'}:mark(c,'punctuation')
        if n.kind=='KtCallExpression':
            target=n.fields.get('function');item=callee(target)
            if item is not None:
                role=resolve(item)
                if role in {'type','enum'} or target.kind=='KtConstructorCalleeExpression':mark(item,'constructor')
                elif n.parent is not None and n.parent.kind in {'KtDotQualifiedExpression','KtSafeQualifiedExpression'} and n.field_name=='selector':mark(item,'method')
                elif role in {'function','method','namespace'} or not any(key(item) in s for s in scopes):mark(item,'function')
            features.add('calls')
        elif n.kind in {'KtDotQualifiedExpression','KtSafeQualifiedExpression'}:
            selector=n.fields.get('selector');item=callee(selector)
            receiver=n.fields.get('receiver');base=reference(receiver) if receiver else None
            if item is not None:
                if base is not None and resolve(base)=='enum' and key(item) in enum_names.get(key(base),set()):mark(item,'enum-member')
                elif selector.kind!='KtCallExpression':mark(item,'constant' if resolve(item)=='constant' else 'property')
            if n.kind=='KtSafeQualifiedExpression':features.add('null-safety')
        elif n.kind=='KtValueArgument':mark(leaf(n.fields.get('label')),'parameter')
        elif n.kind=='KtAnnotationEntry':
            refs=names(n.fields.get('function') or n)
            for item in refs[:-1]:mark(reference(item),'namespace')
            if refs:mark(reference(refs[-1]),'decorator')
            features.add('annotations')
        elif n.kind=='KtAnnotationUseSiteTarget':
            for c in n.children:
                if not c.children and c.start in lexical and lexical[c.start]['kind']=='IDENTIFIER':mark(c,'keyword')
        elif n.kind in {'KtPackageDirective','KtImportDirective'}:
            refs=names(n)
            for item in refs:mark(reference(item),'namespace')
            if n.kind=='KtImportDirective' and refs:bind(reference(refs[-1]),'namespace')
            for c in n.descendants():
                if c.kind=='KtImportAlias':mark(c.fields.get('name'),'namespace',True);bind(c.fields.get('name'),'namespace')
            if refs:features.add('imports')
        elif n.kind=='KtOperationReferenceExpression':
            c=leaf(n)
            if c is not None and c.start in lexical and lexical[c.start]['kind']=='IDENTIFIER' and not lexical[c.start]['keyword']:mark(c,'method')
        elif n.kind=='KtLabeledExpression':mark(leaf(n.fields.get('label')),'label',True)
        if n.kind in {'KtLambdaExpression','KtFunctionLiteral'}:features.add('lambdas')
        if n.kind in {'KtWhenExpression','KtIsExpression','KtDestructuringDeclaration'}:features.add('patterns')
        if n.kind in {'KtSimpleNameStringTemplateEntry','KtBlockStringTemplateEntry'}:features.add('interpolation')
        if n.kind in {'KtNullableType','KtNotNullExpression'}:features.add('null-safety')
        if n.kind=='KtPropertyDelegate':features.add('delegates')
        if n.kind=='KtContextReceiverList':features.add('context-parameters')
        if scoped:scopes.pop()
    visit(tree)
    opaque=sorted((n.start,n.end) for n in tree.descendants() if n.kind=='KtStringTemplateExpression' and not any(c.kind in {'KtSimpleNameStringTemplateEntry','KtBlockStringTemplateEntry'} for c in n.descendants()))
    spans=[];cursor=0
    for t in tokens:
        a,b=t['start'],t['end'];kind=t['kind'];decl=False
        while cursor<len(opaque) and opaque[cursor][1]<=a:cursor+=1
        if cursor<len(opaque) and opaque[cursor][0]<=a<opaque[cursor][1]:
            lo,hi=opaque[cursor]
            if a==lo:spans.append(dict(start=lo,end=hi,tokenType='string'));features.add('strings')
            continue
        if kind=='WHITE_SPACE' or a==b:continue
        if t.get('comment'):role='comment';features.add('comments')
        elif a in roles:role,decl=roles[a]
        elif kind in STRING_PARTS:role='string';features.add('strings')
        elif kind in INTERPOLATION:role='punctuation'
        elif kind in {'INTEGER_LITERAL','INTEGER_CONSTANT','FLOAT_LITERAL','FLOAT_CONSTANT'}:role='number'
        elif t['keyword']:role='keyword'
        elif kind in PUNCTUATION:role='punctuation'
        elif t['operator'] or kind in EXTRA_OPERATORS:role='operator'
        elif kind=='IDENTIFIER':role='keyword' if text(a,b)=='_' else 'variable'
        else:raise ValueError('Unmapped original Kotlin lexer token: '+kind)
        if kind=='IDENTIFIER' and text(a,b).startswith('`'):features.add('backticks')
        if text(a,b)=='suspend' and role=='keyword':features.add('coroutines')
        span=dict(start=a,end=b,tokenType=role)
        if decl:span['modifiers']=['declaration']
        spans.append(span)
    if source.startswith('\ufeff'):spans.append(dict(start=0,end=1,tokenType='punctuation'))
    spans.sort(key=lambda s:s['start']);merged=[];end=0
    for span in spans:
        if span['start']<end or text(end,span['start']).strip():raise ValueError(f'Incomplete original Kotlin Gold at {end}: {span}')
        text(span['start'],span['end'])
        if merged and span['tokenType']=='string' and merged[-1]['tokenType']=='string' and merged[-1]['end']==span['start']:merged[-1]['end']=span['end']
        else:merged.append(span)
        end=span['end']
    if text(end,len(raw)//2).strip():raise ValueError('Unmapped original Kotlin source suffix')
    if profile=='kotlin-script':features.add('scripts')
    if '\r\n' in source:features.add('crlf')
    if any(ord(c)>127 for c in source):features.add('unicode')
    return dict(offsetEncoding='utf-16',spans=merged,features=sorted(features))
