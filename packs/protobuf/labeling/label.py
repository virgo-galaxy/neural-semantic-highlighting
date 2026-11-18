"""Offline CST-local protobuf source roles; no import loading or code generation."""
from .tools import provenance
from .parser import parser
SCALARS={'double','float','int32','int64','uint32','uint64','sint32','sint64','fixed32','fixed64','sfixed32','sfixed64','bool','string','bytes'}
DECL_TYPES={'message_name','service_name'}
def label(*,source,document_kind='protobuf',profile=None):
 if not isinstance(source,str)or document_kind!='protobuf'or(profile or document_kind)!='protobuf':raise ValueError('Expected matching protobuf source kind/profile')
 raw=source.encode('utf-8');provenance()
 if '\x00'in source or '\r'in source.replace('\r\n',''):raise ValueError('Unsupported protobuf control/bare CR')
 bom=3 if raw.startswith(b'\xef\xbb\xbf')else 0
 # BOM is omitted in parse-only bytes, then every result is shifted to original coordinates.
 tree=parser().parse(raw[bom:]);spans=[];features=set();units={0:0};pos=0;u=0
 for c in source:pos+=len(c.encode());u+=len(c.encode('utf-16-le'))//2;units[pos]=u
 def add(a,b,role,mods=()):
  a+=bom;b+=bom
  if a>=b:return
  span=dict(start=units[a],end=units[b],tokenType=role)
  if mods:span['modifiers']=list(mods)
  spans.append(span)
 def ancestors(node):
  while node is not None:yield node;node=node.parent
 def role_for_identifier(node):
  chain=list(ancestors(node));kinds=[x.kind for x in chain];p=node.parent.kind if node.parent else None
  if p in DECL_TYPES:return 'type',['declaration']
  if p=='enum_name':return 'enum',['declaration']
  if p=='rpc_name':return 'method',['declaration']
  if 'package'in kinds:return 'namespace',['declaration']
  if p in {'field','oneof_field','map_field'}:return 'property',['declaration']
  if p=='oneof':return 'label',['declaration']
  if p=='enum_field':return 'enum-member',['declaration']
  if 'message_or_enum_type'in kinds or (p=='full_ident'and node.parent.parent and node.parent.parent.kind=='extend'):return 'type',[]
  # Aggregate option values have object-field keys and enum/identifier values.
  constant=next((n for n in chain if n.kind=='constant'),None)
  if constant is not None and 'full_ident'in kinds[:kinds.index('constant')]:return 'constant',[]
  if 'extension_name'in kinds:
   return ('type'if next(n for n in chain if n.kind=='full_ident').field_name=='type'else 'property'),[]
  if any(k in kinds for k in ['option','field_option','enum_value_option','block_lit']):return 'property',[]
  raise ValueError('Unsupported protobuf identifier context: '+str(kinds))
 def walk(node):
  kind=node.kind
  if kind in {'syntax','edition','import','package','option','message','enum','service','rpc','oneof','map_field','reserved','extensions','extend','group'}:features.add(kind.replace('_','-'))
  if kind=='comment':
   end=node.end-len(node.text.encode())+len(node.text.rstrip('\r\n').encode())if node.text.startswith('//')else node.end
   add(node.start,end,'comment');features.add('comments');return
  if kind=='string'and node.named:
   # Preserve each original quoted literal; comments between concatenated literals stay comments.
   opened=None
   for child in node.children:
    if child.kind in {'"',"'"}:
     if opened is None:opened=child.start
     else:add(opened,child.end,'string');opened=None
    elif child.kind=='comment':
     if opened is not None:raise ValueError('Comment inside original string')
     walk(child)
   if opened is not None:raise ValueError('Incomplete protobuf string')
   features.add('strings');return
  if kind=='reserved_identifier':add(node.start,node.end,'string'if node.text[0]in '\"\''else 'property');return
  if kind in {'int_lit','float_lit'}:add(node.start,node.end,'number');features.add('numbers');return
  # A contiguous signed number is one token. Spaced signs remain operators.
  if kind=='constant':
   cs=[n for n in node.children if n.kind!='comment']
   if len(cs)==2 and cs[0].kind in {'-','+'}and cs[1].kind in {'int_lit','float_lit'}and cs[0].end==cs[1].start:
    add(node.start,node.end,'number');features.add('numbers');return
  if kind=='enum_field':
   # Negative enum integers have the same contiguous sign policy.
   for i,child in enumerate(node.children):
    if child.kind=='-':
     nxt=node.children[i+1]
     if nxt.kind=='int_lit'and child.end==nxt.start:
      for a in node.children[:i]:walk(a)
      add(child.start,nxt.end,'number');features.add('numbers')
      for a in node.children[i+2:]:walk(a)
      return
  if kind=='identifier':
   role,mods=role_for_identifier(node);add(node.start,node.end,role,mods);return
  if not node.children:
   if kind in SCALARS and node.parent and node.parent.kind in {'type','key_type'}:add(node.start,node.end,'type',['default-library'])
   elif kind in {'true','false'}:add(node.start,node.end,'keyword')
   elif not node.named:
    add(node.start,node.end,'operator'if kind in {'=','+','-'}else 'punctuation'if kind in '{}[]()<>,;:./'else 'keyword')
   elif node.end>node.start:raise ValueError('Unsupported protobuf leaf: '+kind)
   return
  for child in node.children:walk(child)
 if bom:spans.append(dict(start=0,end=1,tokenType='punctuation'));features.add('bom')
 walk(tree);spans.sort(key=lambda s:(s['start'],s['end']))
 previous=0;utf16=source.encode('utf-16-le')
 for s in spans:
  if s['start']<previous or utf16[previous*2:s['start']*2].decode('utf-16-le').strip():raise ValueError('Overlapping/incomplete protobuf coverage')
  previous=s['end']
 if utf16[previous*2:].decode('utf-16-le').strip():raise ValueError('Incomplete protobuf suffix')
 if '\r\n'in source:features.add('crlf')
 if any(ord(c)>127 for c in source):features.add('unicode')
 return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
