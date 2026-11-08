"""Pinned offline CMD display labels, without Windows or input execution."""
from functools import lru_cache
import re
from training.shared.offline_tools import load_lexer,provenance
@lru_cache(maxsize=1)
def lexer():
 load_lexer('bat')
 from pygments.lexers.shell import BatchLexer
 from pygments.lexer import bygroups,using,this
 from pygments.token import Name,String,Text,Punctuation
 loop=(r'%%(?:~[a-z]*(?:\$[^:\r\n]+:)?)?[a-z]',Name.Variable)
 class OriginalBatchLexer(BatchLexer):
  tokens={**BatchLexer.tokens,'variable-or-escape':[loop,*BatchLexer.tokens['variable-or-escape']],'string':[loop,*BatchLexer.tokens['string']],
   # Bound FOR /F quote matching to its physical line. The upstream alternative
   # can scan later lines exponentially when a nested command quote closes.
   'for/f':[
    (r'(")([^"\r\n]*")([ \t]*)(\))',bygroups(String.Double,using(this,state='string'),Text,Punctuation)),
    (r"('[^\r\n]*')([ \t]*)(\))(?=[ \t]+do\b)",bygroups(using(this,state='sqstring'),Text,Punctuation)),
    (r'(`[^\r\n]*`)([ \t]*)(\))(?=[ \t]+do\b)',bygroups(using(this,state='bqstring'),Text,Punctuation)),
    *BatchLexer.tokens['for/f'][3:]]}
 return OriginalBatchLexer(stripnl=False,stripall=False,ensurenl=False)

def label(*,source,document_kind='bat',profile='bat'):
 if document_kind!='bat' or profile!='bat' or '\0' in source:raise ValueError('Expected original BAT/CMD source')
 parser=lexer()
 from pygments.token import Token as T
 raw=[];cursor=0
 for a,kind,text in parser.get_tokens_unprocessed(source):
  if not text:continue
  if a!=cursor or source[a:a+len(text)]!=text:raise ValueError('Offline batch lexer changed original source')
  cursor=a+len(text)
  if kind in T.Error and text.strip():raise ValueError('Unsupported CMD token at '+str(a))
  if raw and kind==T.Text and raw[-1][2]==T.Text and raw[-1][1]==a:
   start,_,_,value=raw.pop();raw.append((start,cursor,kind,value+text))
  else:raw.append((a,cursor,kind,text))
 if cursor!=len(source):raise ValueError('Uncovered CMD suffix')
 tokens=[]
 for a,b,kind,text in raw:
  if kind in T.String:
   tokens.append((a,b,kind,text));continue
  if kind==T.Text:
   for m in re.finditer(r'\S+',text):tokens.append((a+m.start(),a+m.end(),kind,m.group()))
  else:
   lo=len(text)-len(text.lstrip());hi=len(text.rstrip())
   if lo<hi:tokens.append((a+lo,a+hi,kind,text[lo:hi]))
 units=[0]
 for char in source:units.append(units[-1]+(2 if ord(char)>65535 else 1))
 output=[];features={'profile:bat'}
 for i,(a,b,kind,text) in enumerate(tokens):
  previous=tokens[i-1][3].lower() if i else None;following=tokens[i+1] if i+1<len(tokens) else None;prefix=source[:a].rsplit('\n',1)[-1];low=text.lower();mods=[]
  if kind in T.Comment or text==':' and following and following[2] in T.Comment and following[0]==b and not prefix.strip():role='comment';features.add('comments')
  elif kind in T.Name.Variable:
   role='variable';features.add('variables')
   if not text.startswith(('%','!')) or text.startswith('%%') and re.search(r'\bfor\b[^\r\n]*$',prefix,re.I) and not re.search(r'\bin\b',prefix,re.I):mods=['declaration']
  elif kind in T.Name.Label:
   role='function';features.add('labels')
   if re.fullmatch(r'\s*:',prefix):mods=['declaration']
  elif kind in T.Keyword:
   role='keyword'
   if low=='for':features.add('loops')
   if low in {'if','else','errorlevel','exist','defined'}:features.add('conditionals')
  elif text==',':role='punctuation'
  elif kind in T.Number:role='number'
  elif kind in T.Operator:role='operator'
  elif kind in T.Punctuation:
   role='operator' if any(c in text for c in '<>|&') else 'punctuation'
  elif kind in T.String:role='string';features.add('strings')
  elif re.fullmatch(r'-?(?:0x[0-9a-f]+|\d+)',low):role='number'
  elif low.startswith(('/','--')):role='parameter'
  elif not prefix.strip().lstrip('@').strip() or previous in {'call','do','&','&&','||','|'}:role='function'
  else:role='string';features.add('strings')
  span={'start':units[a],'end':units[b],'tokenType':role}
  if mods:span['modifiers']=mods
  if role in {'comment','string'} and output and output[-1]['tokenType']==role and output[-1]['end']==span['start']:output[-1]['end']=span['end']
  else:output.append(span)
 if '\r\n' in source:features.add('crlf')
 if any(ord(c)>127 for c in source):features.add('unicode')
 return {'offsetEncoding':'utf-16','spans':output,'features':sorted(features)}
