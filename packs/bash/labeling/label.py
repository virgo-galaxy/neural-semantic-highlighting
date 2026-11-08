"""Offline original-coordinate Shell teacher; never imported by inference."""
from __future__ import annotations
import re
from functools import lru_cache
from training.shared.offline_tools import load_lexer, provenance

PROFILES={'posix','bash','zsh','csh'}
IDENTIFIER=re.compile(r'[A-Za-z_][A-Za-z_0-9-]*\Z')
NUMBER=re.compile(r'(?:0[xX][0-9a-fA-F]+|[0-9]+(?:\.[0-9]+)?)\Z')
FLAG=re.compile(r'--?(?:[A-Za-z][A-Za-z0-9_-]*(?:=.*)?|-)\Z')

@lru_cache(maxsize=2)
def lexer(profile):return load_lexer('tcsh' if profile=='csh' else 'bash')

def label(*,source,document_kind='bash',profile='bash'):
    if document_kind!='bash' or profile not in PROFILES or '\0' in source:raise ValueError('Expected original Shell source and known offline profile')
    parser=lexer(profile)
    from pygments.token import Token as T
    # Importing token types follows opening the isolated lexer; no system package.
    def original_tokens():
        for a,kind,text in parser.get_tokens_unprocessed(source):
            if profile=='csh' and kind in T.Literal.String.Double:
                # Common quoted variable syntax must have identical labels in
                # a shared model, rather than inherit lexer-specific chunking.
                for offset,subkind,value in lexer('bash').get_tokens_unprocessed(text):
                    yield a+offset,subkind,value
            else:yield a,kind,text
    tokens=[];cursor=0
    for a,kind,text in original_tokens():
        if not text:continue
        if a!=cursor or source[a:a+len(text)]!=text:raise ValueError('Lexer changed or skipped original source')
        cursor=a+len(text)
        if kind in T.Error and text.strip():raise ValueError('Unsupported Shell lexical token at '+str(a))
        if kind in T.Literal.String:
            tokens.append((a,cursor,kind,text));continue
        if kind in T.Text and ('<' in text or '>' in text) and not (profile=='zsh' and re.search(r'<[0-9]*-[0-9]*>',text)):
            for match in re.finditer(r'<<<|<<-?|<|>>?|[^<>]+',text):
                value=match[0]
                lo=len(value)-len(value.lstrip());hi=len(value.rstrip())
                if lo<hi:tokens.append((a+match.start()+lo,a+match.start()+hi,T.Operator if value[0] in '<>' else kind,value[lo:hi]))
            continue
        # Tokenizers sometimes attach surrounding whitespace to keywords or
        # comments. Trim only those exteriors, retaining original coordinates.
        leading=len(text)-len(text.lstrip());trailing=len(text.rstrip())
        if leading<trailing:
            value=text[leading:trailing]
            if profile=='csh' and kind in T.Text and len(value)>1 and value.endswith(':'):
                tokens.extend([(a+leading,a+trailing-1,kind,value[:-1]),(a+trailing-1,a+trailing,kind,':')])
            else:tokens.append((a+leading,a+trailing,kind,value))
    if cursor!=len(source):raise ValueError('Uncovered source suffix')
    combined=[]
    for entry in tokens:
        if combined and combined[-1][1]==entry[0] and combined[-1][3]+entry[3] in {';;',';&',';;&','[[',']]','>&','<&','&>','&>>'}:
            lo,hi,kind,text=combined.pop();combined.append((lo,entry[1],kind,text+entry[3]))
        else:combined.append(entry)
    tokens=combined
    definitions={};bindings=set();declared_variables=set()
    for i,(a,b,kind,text) in enumerate(tokens):
        upcoming=[item[3] for item in tokens[i+1:i+4]]
        if IDENTIFIER.fullmatch(text) and (upcoming[:3]==['(',')','{'] or (i and tokens[i-1][3]=='function')):
            definitions[(a,b)]=text
        if kind in T.Name.Variable and i+1<len(tokens) and tokens[i+1][3] in {'=','+='}:
            declared_variables.add((a,b))
        if text in {'for','select','foreach'} and i+1<len(tokens):
            lo,hi,k,name=tokens[i+1]
            if IDENTIFIER.fullmatch(name):bindings.add((lo,hi))
    function_names=set(definitions.values());units=[0]
    for char in source:units.append(units[-1]+(2 if ord(char)>65535 else 1))
    output=[];command=True;assignment=False;binding_mode=False;redirection=False;word_list=False;case_mode=False;case_pattern=False
    substitutions=[];arithmetic=False;arrays=[];conditional=False;csh_condition=False
    quote=None;quote_parent=False
    expansions=[]
    csh_math=False
    features={'profile:'+profile};last_end=0;last_word=None
    for index,(a,b,kind,text) in enumerate(tokens):
        gap=source[last_end:a]
        if '\n' in gap or '\r' in gap:
            command=True;assignment=False;binding_mode=False;redirection=False
            if csh_math:arithmetic=False;csh_math=False
        mods=[];role=None
        if profile=='csh' and text=='@' and command:
            role='operator';csh_math=True;arithmetic=True;command=False
        elif csh_math and text in {'+','-','*','/','%','++','--','+=','-=','*=','/=','%='}:role='operator'
        elif text in {'[','[['} and command and not kind in T.Literal.String:
            role='punctuation';conditional=True;command=False
        elif text in {']',']]'} and conditional:
            role='punctuation';conditional=False;command=False
        elif conditional and text in {'-eq','-ne','-lt','-gt','-le','-ge','-f','-d','-e','-r','-w','-x','-n','-z'}:role='operator'
        elif csh_condition and text in {'>','<','==','!=','>=','<=','&&','||'}:role='operator'
        elif text in {'>','>>','<','<<','<<-','<<<','>&','<&','&>'} and not kind in T.Literal.String:
            role='operator';redirection=True
        elif kind in T.Keyword and text in {'$(', '$(('}:
            substitutions.append((command if assignment else False,binding_mode,arithmetic,quote,quote_parent))
            arithmetic=text=='$((';command=not arithmetic;assignment=False;binding_mode=False
            quote=None
            role='operator';features.add('command-substitution' if text=='$(' else 'arithmetic')
        elif kind in T.Keyword and text in {')','))'} and substitutions:
            command,binding_mode,arithmetic,quote,quote_parent=substitutions.pop();role='punctuation';assignment=False
        elif text=='${' and kind in T.Literal.String.Interpol:
            expansions.append(command if assignment else False);command=False;assignment=False;role='operator'
            features.add('parameter-expansion')
        elif text=='}' and expansions and kind in T.Literal.String.Interpol:
            command=expansions.pop();role='operator'
        elif expansions and kind in T.Keyword:role='operator'
        elif profile=='csh' and text==':' and case_pattern:
            role='punctuation';case_pattern=False;command=True
        elif (a,b) in definitions:role='function';mods=['declaration'];features.add('functions');command=False
        elif (a,b) in bindings:role='variable';mods=['declaration'];command=False
        elif kind in T.Comment:role='comment';features.add('comments')
        elif kind in T.Literal.String:
            role='string';features.add('strings')
            delimiter='"' if kind in T.Literal.String.Double else "'" if kind in T.Literal.String.Single else None
            if delimiter and quote==delimiter and text.endswith(delimiter):
                quote=None;command=quote_parent
            elif delimiter and quote is None and text.startswith(delimiter) and (len(text)==1 or not text.endswith(delimiter)):
                quote=delimiter;quote_parent=command if assignment else False
                command=False;assignment=False
            elif not quote:
                if assignment:assignment=False
                elif command:command=False
        elif kind in T.Name.Variable:
            role='variable';features.add('variables')
            if (a,b) in declared_variables:mods=['declaration'];assignment=True
            elif assignment:assignment=False
            elif command:command=False
        elif kind in T.Literal.Number:role='number'
        elif command and text in {'break','continue','return','exit','breaksw'} and text not in function_names:
            role='keyword';command=False
        elif kind in T.Keyword:
            if not command and not (text=='in' and (word_list or case_mode)) and not (text=='esac' and case_mode):role='string'
            else:
                role='keyword'
                if text in {'then','do','else','elif','if','while','until','repeat','time','coproc','!'}:command=True;word_list=False
                elif text in {'for','foreach','select','case','in','esac','fi','done','end','endif','switch','endsw'}:command=False
                if text in {'for','foreach','select'}:word_list=True
                if text=='if' and profile=='csh':csh_condition=True
                if text=='case':case_mode=True;case_pattern=profile=='csh'
                elif text=='default' and profile=='csh' and case_mode:case_pattern=True;command=False
                elif text=='in' and case_mode:case_pattern=True
                elif text in {'esac','endsw'}:case_mode=False;case_pattern=False
        elif kind in T.Operator or kind in T.Punctuation:
            role=('punctuation' if text in {'(',')','{','}',';',',',';;',';&',';;&'} else
                  'operator' if kind in T.Operator or text in {'|','||','&&','&','$','!','[',']','>','<','>&','<&','&>','&>>'} else 'string')
            if text in {';',';;',';&',';;&','|','||','&&','&','{','}'}:
                command=True;binding_mode=False;assignment=False;redirection=False
                if csh_math:arithmetic=False;csh_math=False
            if text in {';;',';&',';;&'} and case_mode:command=False;case_pattern=True
            elif text=='|' and case_pattern:command=False
            elif text in {'>','>>','<','<<','<<-','<<<','>&','<&','&>'}:redirection=True
            elif text=='(' and assignment:
                if not csh_math:arrays.append(command);features.add('arrays')
                command=False;assignment=False
            elif text=='(' and not word_list:command=True
            elif text==')':
                command=arrays.pop() if arrays else case_mode or csh_condition
                word_list=False;case_pattern=False;csh_condition=False
            if text in {'|','||','&&'}:features.add('pipelines')
        elif kind in T.Name.Builtin or kind in T.Text or kind in T.Name:
            if NUMBER.fullmatch(text):role='number';assignment=False
            elif arithmetic and IDENTIFIER.fullmatch(text):role='variable'
            elif FLAG.fullmatch(text) or text=='--':role='parameter'
            elif assignment or redirection:role='string';assignment=False;redirection=False
            elif binding_mode and not arrays and IDENTIFIER.fullmatch(text):
                role='variable';mods=['declaration']
                if binding_mode=='one':binding_mode=False
            elif command:
                role='function';command=False
                if kind in T.Name.Builtin and text not in function_names:mods=['default-library']
                if text in {'local','declare','typeset','readonly','export','setenv'}:binding_mode='one' if text=='setenv' else True
            else:role='string'
        else:raise ValueError('Unmapped Shell token '+str(kind))
        if role is None:raise ValueError('Missing Shell role')
        if role=='keyword':
            if text in {'if','elif','then','else','endif'}:features.add('conditionals')
            if text in {'for','foreach','select','while','until'}:
                features.add('loops')
                if a==0:features.add('leading-loops')
            if text in {'case','switch','esac','endsw'}:features.add('branches')
        span={'start':units[a],'end':units[b],'tokenType':role}
        if mods:span['modifiers']=mods
        if output and role=='string' and output[-1]['tokenType']=='string' and output[-1]['end']==units[a]:output[-1]['end']=units[b]
        else:output.append(span)
        last_end=b;last_word=text
    if '\r\n' in source:features.add('crlf')
    if any(ord(char)>127 for char in source):features.add('unicode')
    return {'offsetEncoding':'utf-16','spans':output,'features':sorted(features)}
