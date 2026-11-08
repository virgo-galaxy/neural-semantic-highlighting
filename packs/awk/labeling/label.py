"""Pinned offline AWK tokenization and source-local roles; never run input."""
from functools import lru_cache
import re
from training.shared.offline_tools import load_lexer,provenance

CONTROL=set('BEGIN END BEGINFILE ENDFILE if else while do for break continue return exit switch case default print printf getline next nextfile delete'.split())
BUILTINS=set('atan2 cos exp int log rand sin sqrt srand gensub gsub index length match split sprintf sub substr tolower toupper close fflush strftime systime system asort asorti and compl lshift or rshift xor strtonum mktime patsplit isarray typeof bindtextdomain dcgettext dcngettext'.split())
VARIABLES=set('ARGC ARGIND ARGV BINMODE CONVFMT ENVIRON ERRNO FIELDWIDTHS FILENAME FNR FPAT FS FUNCTAB IGNORECASE LINT NF NR OFMT OFS ORS PREC PROCINFO RLENGTH ROUNDMODE RS RSTART RT SUBSEP SYMTAB TEXTDOMAIN'.split())

@lru_cache(maxsize=1)
def lexer():
    load_lexer('awk')
    from pygments.lexers.textedit import AwkLexer
    from pygments.token import Keyword,Name,Operator,String
    class OriginalAwkLexer(AwkLexer):
        tokens={**AwkLexer.tokens,
        'slashstartsregex':[(r'\\(?=\r?\n)',Operator),*AwkLexer.tokens['slashstartsregex']],
        'root':[
            (r'@(include|load|namespace)\b',Keyword),
            (r'(switch|case|default|BEGINFILE|ENDFILE)\b',Keyword,'slashstartsregex'),
            (r'@/(?:\\.|[^/\\\n])*/',String.Regex),
            (r'@|\\(?=\r?\n)',Operator),
            (r'\|&',Operator,'slashstartsregex'),
            (r'[A-Za-z_]\w*(?:::[A-Za-z_]\w*)+',Name.Other),
            *AwkLexer.tokens['root'],
        ]}
    return OriginalAwkLexer(stripnl=False,stripall=False,ensurenl=False)

def label(*,source,document_kind='awk',profile='awk'):
    if document_kind!='awk' or profile!='awk' or '\0' in source:raise ValueError('Expected original AWK source')
    parser=lexer()
    from pygments.token import Token as T
    tokens=[];cursor=0
    for a,kind,text in parser.get_tokens_unprocessed(source):
        if not text:continue
        if a!=cursor or source[a:a+len(text)]!=text:raise ValueError('Offline lexer changed original AWK source')
        cursor=a+len(text)
        if kind in T.Error and text.strip():raise ValueError('Unsupported AWK token at '+str(a))
        if kind in T.String:
            tokens.append((a,cursor,kind,text));continue
        lo=len(text)-len(text.lstrip());hi=len(text.rstrip())
        if lo<hi:tokens.append((a+lo,a+hi,kind,text[lo:hi]))
    if cursor!=len(source):raise ValueError('Uncovered AWK suffix')
    # Static/dynamic single-word field references share one source span.
    combined=[]
    for entry in tokens:
        if combined and combined[-1][3]=='$' and combined[-1][1]==entry[0] and (entry[2] in T.Name or entry[2] in T.Number):
            start,_,_,_=combined.pop();combined.append((start,entry[1],T.Name.Variable,'$'+entry[3]))
        else:combined.append(entry)
    tokens=combined;definitions=set();parameters=set();function_names=set()
    for i,entry in enumerate(tokens):
        if i and tokens[i-1][3]=='function':
            definitions.add(i);function_names.add(entry[3]);j=i+1
            if j<len(tokens) and tokens[j][3]=='(':
                j+=1
                while j<len(tokens) and tokens[j][3]!=')':
                    if tokens[j][2] in T.Name:parameters.add(j)
                    j+=1
    units=[0]
    for char in source:units.append(units[-1]+(2 if ord(char)>65535 else 1))
    output=[];features={'profile:awk'}
    for i,(a,b,kind,text) in enumerate(tokens):
        following=tokens[i+1][3] if i+1<len(tokens) else None
        previous=tokens[i-1][3] if i else None
        mods=[]
        if kind in T.Comment:role='comment';features.add('comments')
        elif kind in T.String.Regex:role='regexp';features.add('regexps')
        elif kind in T.String:role='string';features.add('strings')
        elif kind in T.Number:role='number'
        elif i in definitions:role='function';mods=['declaration'];features.add('functions')
        elif i in parameters:role='variable';mods=['declaration']
        elif text=='function' or text in CONTROL or text.startswith(('@include','@load','@namespace')):role='keyword'
        elif kind in T.Operator:role='operator'
        elif kind in T.Punctuation:role='punctuation'
        elif kind in T.Name:
            if text in VARIABLES:role='variable';mods=['default-library']
            elif text.startswith('$'):role='variable';features.add('fields')
            elif previous=='@':role='variable'
            elif following=='(' or text in function_names or text in BUILTINS:
                role='function'
                if text in BUILTINS and text not in function_names:mods=['default-library']
            else:role='variable'
        elif kind in T.Keyword and text in BUILTINS:role='function';mods=['default-library']
        else:raise ValueError('Unmapped AWK token '+str(kind))
        if role=='keyword':
            if text in {'if','else','switch','case','default'}:features.add('conditionals')
            if text in {'while','do','for'}:features.add('loops')
            if text in {'BEGIN','END','BEGINFILE','ENDFILE'}:features.add('phases')
        item={'start':units[a],'end':units[b],'tokenType':role}
        if mods:item['modifiers']=mods
        output.append(item)
    if '\r\n' in source:features.add('crlf')
    if any(ord(c)>127 for c in source):features.add('unicode')
    return {'offsetEncoding':'utf-16','spans':output,'features':sorted(features)}
