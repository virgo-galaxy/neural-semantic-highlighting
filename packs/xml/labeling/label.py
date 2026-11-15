"""Offline original XML ranges, independently validated by Expat twice."""
import re
from xml.parsers import expat
from .tools import provenance
NAME=re.compile(r'[^\s<>=/?!\[\]"\']+')
ENTITY=re.compile(r'&(?:amp|lt|gt|quot|apos|#[0-9]+|#x[0-9a-fA-F]+);')
SPACE=' \t\r\n'
def label(*,source,document_kind='xml',profile=None):
 if not isinstance(source,str)or document_kind not in {'xml','svg'}or(profile or document_kind)!=document_kind:raise ValueError('Expected matching XML/SVG source kind/profile')
 source.encode('utf-8');provenance();spans=[];features=set();events=[];units=[0];i=0
 for c in source:units.append(units[-1]+len(c.encode('utf-16-le'))//2)
 def add(a,b,r,closing=False):
  if b<=a:return
  s=dict(start=units[a],end=units[b],tokenType=r)
  if closing:s['modifiers']=['closing']
  spans.append(s)
  f={'tag':'tags','attribute':'attributes','string':'strings','text':'text','entity':'entities','comment':'comments'}.get(r)
  if f:features.add(f)
 def space(a):
  while a<len(source)and source[a]in SPACE:a+=1
  return a
 if source.startswith('\ufeff'):add(0,1,'punctuation');i=1;features.add('bom')
 while i<len(source):
  if source.startswith('<!--',i):
   j=source.find('-->',i+4)
   if j<0:raise ValueError('Unclosed XML comment')
   add(i,j+3,'comment');i=j+3
  elif source.startswith('<![CDATA[',i):
   j=source.find(']]>',i+9)
   if j<0:raise ValueError('Unclosed CDATA')
   add(i,j+3,'string');features.add('cdata');i=j+3
  elif source.startswith('<?',i):
   j=source.find('?>',i+2)
   if j<0:raise ValueError('Unclosed processing instruction')
   add(i,j+2,'keyword');features.add('instructions');i=j+2
  elif source.startswith('<!DOCTYPE',i):
   j=i+9;quote=None;depth=0
   while j<len(source):
    c=source[j]
    if quote:
     if c==quote:quote=None
    elif c in '\"\'':quote=c
    elif source.startswith('<!--',j):
     end=source.find('-->',j+4)
     if end<0:raise ValueError('Unclosed DTD comment')
     j=end+2
    elif c=='[':depth+=1
    elif c==']':depth-=1
    elif c=='>'and depth==0:break
    j+=1
   if j==len(source):raise ValueError('Unclosed doctype')
   add(i,j+1,'keyword');features.add('doctype');i=j+1
  elif source[i]=='<':
   closing=source.startswith('</',i);a=i+2 if closing else i+1;add(i,a,'punctuation');m=NAME.match(source,a)
   if not m:raise ValueError('Missing XML name')
   name=m[0];add(a,m.end(),'tag',closing);i=m.end();attrs=[]
   if ':'in name:features.add('namespaces')
   while True:
    before=i;i=space(i)
    if source.startswith('/>',i)and not closing:
     add(i,i+2,'punctuation');events.extend([('start',name,attrs),('end',name)]);features.add('empty-elements');i+=2;break
    if i<len(source)and source[i]=='>':
     add(i,i+1,'punctuation');events.append(('end',name)if closing else('start',name,attrs));i+=1;break
    if closing or i==before:raise ValueError('Invalid tag or missing attribute whitespace')
    m=NAME.match(source,i)
    if not m:raise ValueError('Missing attribute name')
    attr=m[0];attrs.append(attr);add(i,m.end(),'attribute');i=space(m.end())
    if attr=='xmlns'or':'in attr:features.add('namespaces')
    if i>=len(source)or source[i]!='=':raise ValueError('Missing XML attribute equals')
    add(i,i+1,'punctuation');i=space(i+1)
    if i>=len(source)or source[i]not in '\"\'':raise ValueError('XML attributes require quotes')
    j=source.find(source[i],i+1)
    if j<0:raise ValueError('Unclosed XML attribute')
    add(i,j+1,'string');i=j+1
  else:
   j=source.find('<',i);j=len(source)if j<0 else j
   cursor=i
   for m in ENTITY.finditer(source,i,j):
    if source[cursor:m.start()].strip():add(cursor,m.start(),'text')
    add(m.start(),m.end(),'entity');cursor=m.end()
   if source[cursor:j].strip():add(cursor,j,'text')
   i=j
 # Expat independently checks nesting, complete syntax, legal references and names.
 # Namespace mode additionally rejects unbound prefixes/duplicate expanded attrs.
 # A validation-only wrapper accepts editor fragments but never shifts output.
 document=source
 if not any(e[0]=='start'for e in events):document='<nsh-root>'+source.lstrip('\ufeff')+'</nsh-root>'
 for namespace in [None,'|']:
  parser=expat.ParserCreate(namespace_separator=namespace);parser.ordered_attributes=True;actual=[]
  if namespace is None:
   parser.StartElementHandler=lambda n,a:actual.append(('start',n,a[::2]))
   parser.EndElementHandler=lambda n:actual.append(('end',n))
  def reject_entity(*args):raise ValueError('Custom entity declarations are outside bounded XML supervision')
  def declaration(version,encoding,standalone):
   if version!='1.0':raise ValueError('Only XML 1.0 is in scope')
   if encoding and encoding.lower().replace('-','')not in {'utf8','usascii'}:raise ValueError('Only original UTF-8 source is in scope')
  parser.EntityDeclHandler=reject_entity;parser.XmlDeclHandler=declaration
  parser.ExternalEntityRefHandler=lambda *args:1
  parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
  try:parser.Parse(document,True)
  except expat.ExpatError as error:raise ValueError('Invalid XML: '+str(error))from error
  if namespace is None and document==source and actual!=events:raise ValueError('Original tag/attribute ranges disagree with Expat')
 previous=0;raw=source.encode('utf-16-le')
 for s in spans:
  if s['start']<previous or raw[previous*2:s['start']*2].decode('utf-16-le').strip():raise ValueError('Incomplete/overlapping XML source coverage')
  previous=s['end']
 if raw[previous*2:].decode('utf-16-le').strip():raise ValueError('Incomplete XML source suffix')
 if '\r\n'in source:features.add('crlf')
 if any(ord(c)>127 for c in source):features.add('unicode')
 return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
