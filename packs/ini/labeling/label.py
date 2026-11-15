"""Offline source-local INI ranges, independently structure-checked by ConfigParser."""
import configparser,hashlib,re
from .tools import provenance
NUMBER=re.compile(r'[+-]?(?:0[xX][0-9a-fA-F]+|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\Z',re.ASCII)
BOOLEANS={'true','false','yes','no','on','off'}
def label(*,source,document_kind='ini',profile=None):
 if not isinstance(source,str) or document_kind!='ini' or (profile or document_kind)!='ini':raise ValueError('Expected matching INI source kind/profile')
 source.encode('utf-8');provenance()
 if any(ord(c)<32 and c not in '\t\r\n' for c in source) or '\x7f'in source or '\r'in source.replace('\r\n',''):raise ValueError('Unsupported INI control or bare CR')
 original=source;spans=[];features=set();units=[0]
 for char in source:units.append(units[-1]+len(char.encode('utf-16-le'))//2)
 def add(start,end,role):
  if end>start:spans.append(dict(start=units[start],end=units[end],tokenType=role))
  if role=='property':features.add('properties')
  if role in {'string','number','keyword','comment'}:features.add({'string':'strings','number':'numbers','keyword':'keywords','comment':'comments'}[role])
 offset=0
 if source.startswith('\ufeff'):add(0,1,'punctuation');offset=1;source=source[1:];features.add('bom')
 # Synthetic root is validation-only; no source offsets or output text are changed.
 root='__nsh_root_'+hashlib.sha256(source.encode()).hexdigest()
 while root in source:root+='_' 
 default=root+'_defaults';expected={root:set()};section=root;indent=None;has_option=False;valueless=False
 for physical in source.splitlines(keepends=True):
  # Non-ASCII line separators are ordinary value characters, not physical lines.
  if not physical.endswith('\n') and ('\u2028'in physical or '\u2029'in physical or '\x85'in physical):raise ValueError('Unsupported INI line separator')
  content=physical[:-2] if physical.endswith('\r\n') else physical[:-1] if physical.endswith('\n') else physical
  lo=len(content)-len(content.lstrip(' \t'));hi=len(content.rstrip(' \t'));text=content[lo:hi];start=offset+lo
  if not text:offset+=len(physical);continue
  if text[0]in '#;':add(start,offset+hi,'comment');offset+=len(physical);continue
  if has_option and lo>indent:
   if valueless:raise ValueError('Valueless INI option cannot have continuation')
   add(start,offset+hi,'string');features.add('continuations');offset+=len(physical);continue
  if text.startswith('['):
   stop=text.rfind(']')
   if stop<=1:raise ValueError('Invalid INI section header')
   suffix=text[stop+1:];tail=suffix.lstrip(' \t')
   if tail and tail[0]not in '#;':raise ValueError('Unexpected text after INI header')
   add(start,start+1,'punctuation');add(start+1,start+stop,'namespace');add(start+stop,start+stop+1,'punctuation')
   if tail:add(start+stop+1+len(suffix)-len(tail),offset+hi,'comment')
   section=text[1:stop];expected.setdefault(section,set());features.add('sections');has_option=False;indent=None
  else:
   delim=next((i for i,c in enumerate(text)if c in '=:'),None)
   key=text if delim is None else text[:delim].rstrip(' \t')
   if not key:raise ValueError('Empty INI option name')
   add(start,start+len(key),'property');expected[section].add(key);has_option=True;indent=lo;valueless=delim is None
   if delim is None:features.add('valueless')
   else:
    add(start+delim,start+delim+1,'punctuation');value=text[delim+1:];trim=len(value)-len(value.lstrip(' \t'));value=value[trim:]
    role='keyword'if value.lower()in BOOLEANS else 'number'if NUMBER.fullmatch(value)else 'string'
    if value:add(start+delim+1+trim,offset+hi,role)
    else:features.add('empty-values')
  offset+=len(physical)
 if offset!=len(original):raise ValueError('INI physical line ranges diverged')
 parser=configparser.ConfigParser(interpolation=None,strict=False,allow_no_value=True,delimiters=('=',':'),comment_prefixes=('#',';'),inline_comment_prefixes=None,empty_lines_in_values=True,default_section=default)
 parser.optionxform=str
 try:parser.read_string('['+root+']\n'+source)
 except (configparser.Error,AttributeError,ValueError)as error:raise ValueError('Invalid INI structure: '+str(error))from error
 # No values are retrieved or interpolated, and DEFAULT remains an ordinary section.
 actual={name:set(parser[name])for name in parser.sections()}
 if actual!=expected:raise ValueError('Original INI ranges disagree with independent ConfigParser structure')
 previous=0;raw=original.encode('utf-16-le')
 for span in spans:
  if span['start']<previous or raw[previous*2:span['start']*2].decode('utf-16-le').strip():raise ValueError('Incomplete/overlapping INI coverage')
  previous=span['end']
 if raw[previous*2:].decode('utf-16-le').strip():raise ValueError('Incomplete INI suffix')
 if '\r\n'in original:features.add('crlf')
 if any(ord(c)>127 for c in original):features.add('unicode')
 return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
