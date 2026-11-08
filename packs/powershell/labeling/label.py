"""Pinned offline PowerShell display lexer; never install or invoke pwsh/.NET."""
from functools import lru_cache
import re
from training.shared.offline_tools import load_lexer,provenance
KEYWORDS=set('begin break catch class clean configuration continue data default do dynamicparam else elseif end enum exit filter finally for foreach from function if in param process return switch throw trap try until using var while workflow parallel sequence hidden static base'.split())
AUTOMATIC=set('args error executioncontext false home host input lastexitcode matches myinvocation null pid profile psboundparameters pscmdlet psculture psitem psscriptroot pscommandpath psversiontable pwd shellid stacktrace this true _ ? ^ $'.split())
OPERATORS='and or xor not band bor bxor bnot shl shr eq ne gt ge lt le ceq cne cgt cge clt cle ieq ine igt ige ilt ile like notlike clike cnotlike ilike inotlike match notmatch cmatch cnotmatch imatch inotmatch contains notcontains ccontains cnotcontains icontains inotcontains in notin cin cnotin iin inotin replace creplace ireplace split csplit isplit join is isnot as f'.split()
@lru_cache(maxsize=1)
def lexer():
 load_lexer('powershell')
 from pygments.lexer import RegexLexer,words
 from pygments.token import Text,Comment,String,Number,Name,Operator,Punctuation,Error
 class DisplayPowerShell(RegexLexer):
  flags=re.MULTILINE|re.DOTALL|re.IGNORECASE
  tokens={'root':[
   (r'\s+',Text),(r'<#',Comment,'block'),(r'#[^\r\n]*',Comment),
   (r'@"[ \t]*\r?\n.*?^"@',String.Heredoc),
   (r"@'[ \t]*\r?\n.*?^'@",String.Heredoc),
   (r'"(?:`[\s\S]|""|[^"`])*"',String.Double),
   (r"'(?:''|[^'])*'",String.Single),
   (r'\$\{[^}\r\n]+\}|\$(?:[\w]+:)?[\w]+|\$[?^$]|@[A-Za-z_]\w*',Name.Variable),
   (r'\[(?:[A-Za-z_][\w.\[\], `+]*\??)\]',Name.Class),
   (words(OPERATORS,prefix=r'-',suffix=r'\b'),Operator),
   (r'(?<!\w)(?:0x[0-9a-f]+|0b[01]+|(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)(?:u?l|d|n|kb|mb|gb|tb|pb)?\b',Number),
   (r'-[A-Za-z_]\w*(?:-[A-Za-z_]\w*)*',Name.Attribute),
   (r'[A-Za-z_][\w-]*(?::[\w-]+)?',Name),
   (r'`[\s\S]',Punctuation),
   (r'\?\?=?|\?\.|&&|\|\||::|\.\.|\+\+|--|[+*/%!=<>-]=?|[|&?]',Operator),
   (r'[{}()[\],;:.@\\$]',Punctuation),
   (r'[^\w\s]',Text),
  ],'block':[(r'<#',Comment,'#push'),(r'#>',Comment,'#pop'),(r'(?:(?!<#|#>)[\s\S])+',Comment)]}
 return DisplayPowerShell(stripnl=False,stripall=False,ensurenl=False)

def label(*,source,document_kind='powershell',profile='powershell'):
 if document_kind!='powershell' or profile!='powershell' or '\0' in source:raise ValueError('Expected original PowerShell source')
 parser=lexer()
 from pygments.token import Token as T
 tokens=[];cursor=0
 for a,kind,text in parser.get_tokens_unprocessed(source):
  if not text:continue
  if a!=cursor or source[a:a+len(text)]!=text:raise ValueError('Offline lexer changed source')
  cursor=a+len(text)
  if kind in T.Error:raise ValueError('Unsupported PowerShell token')
  if kind in T.String or kind in T.Comment:tokens.append((a,cursor,kind,text));continue
  lo=len(text)-len(text.lstrip());hi=len(text.rstrip())
  if lo<hi:tokens.append((a+lo,a+hi,kind,text[lo:hi]))
 if cursor!=len(source):raise ValueError('Uncovered PowerShell suffix')
 definitions={};parameters=set();depth=0;param_depth=None
 for i,(a,b,kind,text) in enumerate(tokens):
  prior=tokens[i-1][3].lower() if i else '';low=text.lower()
  if prior in {'function','filter','workflow','class','enum'}:definitions[i]='type' if prior in {'class','enum'} else 'function'
  if low=='param' and i+1<len(tokens) and tokens[i+1][3]=='(':param_depth=depth+1
  if text=='(':depth+=1
  if kind in T.Name.Variable and param_depth is not None and depth==param_depth:parameters.add(i)
  if text==')':
   if param_depth==depth:param_depth=None
   depth-=1
 defined_names={tokens[i][3].lower() for i,role in definitions.items() if role=='function'}
 units=[0]
 for char in source:units.append(units[-1]+(2 if ord(char)>65535 else 1))
 output=[];features={'profile:powershell'}
 for i,(a,b,kind,text) in enumerate(tokens):
  prior=tokens[i-1][3] if i else None;following=tokens[i+1][3] if i+1<len(tokens) else None;low=text.lower();mods=[]
  if kind in T.Comment:role='comment';features.add('comments')
  elif kind in T.String:
   role='string';features.add('strings')
   if kind in T.String.Heredoc:features.add('here-strings')
  elif kind in T.Number:role='number'
  elif i in definitions:role=definitions[i];mods=['declaration'];features.add('functions')
  elif kind in T.Name.Variable:
   role='variable'
   if low.lstrip('$') in AUTOMATIC:mods=['default-library']
   elif i in parameters or following in {'=','+=','-='}:mods=['declaration']
  elif kind in T.Name.Class:role='type';features.add('types')
  elif kind in T.Name.Attribute:role='parameter';features.add('parameters')
  elif low in KEYWORDS:role='keyword'
  elif kind in T.Operator:role='operator'
  elif kind in T.Punctuation:role='punctuation'
  elif kind in T.Name:
   if prior in {'.','?.','::'}:role='function' if following=='(' else 'property'
   elif following=='=' and prior not in {'.','?.','::'}:role='property'
   elif re.fullmatch('[a-z]+-[a-z][a-z0-9-]*',low):role='function';mods=[] if low in defined_names else ['default-library']
   elif following=='(' or prior in {'|','&',';','{','=','return'} or not source[:a].split('\n')[-1].strip():role='function'
   elif prior=='using':role='namespace'
   else:role='string'
  else:role='string'
  if text=='|':features.add('pipelines')
  if text=='@' and following=='{':features.add('hashtables')
  span={'start':units[a],'end':units[b],'tokenType':role}
  if mods:span['modifiers']=mods
  if role=='comment' and output and output[-1]['tokenType']==role and output[-1]['end']==span['start']:output[-1]['end']=span['end']
  else:output.append(span)
 if '\r\n' in source:features.add('crlf')
 if any(ord(c)>127 for c in source):features.add('unicode')
 return {'offsetEncoding':'utf-16','spans':output,'features':sorted(features)}
