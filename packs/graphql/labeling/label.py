"""Offline GraphQL AST roles projected onto complete original lexical ranges."""
from .tools import provenance
BUILTINS={'Int','Float','String','Boolean','ID'}
DECL_TYPES={'scalar_type_definition','object_type_definition','interface_type_definition','union_type_definition','input_object_type_definition'}
def label(*,source,document_kind='graphql',profile=None):
 if not isinstance(source,str)or document_kind!='graphql'or(profile or document_kind)!='graphql':raise ValueError('Expected matching GraphQL kind/profile')
 source.encode('utf-8');provenance()
 from graphql import parse,GraphQLError
 from graphql.language import Lexer,Source,TokenKind
 from graphql.language.ast import Node
 # Empty editors/comments are valid highlighting inputs without a definition AST.
 lexer=Lexer(Source(source));tokens=[];start=0
 try:
  while True:
   token=lexer.read_next_token(start)
   if token.kind==TokenKind.EOF:break
   tokens.append(token);start=token.end
  ast=parse(source)if any(t.kind!=TokenKind.COMMENT for t in tokens)else None
 except GraphQLError as error:raise ValueError('Unsupported/invalid GraphQL syntax: '+str(error))from error
 roles={};features=set();units=[0]
 for c in source:units.append(units[-1]+len(c.encode('utf-16-le'))//2)
 def assign(node,role,*mods):
  if node is not None:roles[(node.loc.start,node.loc.end)]=(role,list(mods))
 def walk(node,parent=None,key=None):
  if not isinstance(node,Node):return
  kind=node.kind
  if kind in DECL_TYPES:assign(node.name,'type','declaration');features.add('schema')
  elif kind in {k.replace('_definition','_extension')for k in DECL_TYPES}:assign(node.name,'type');features.add('extensions')
  elif kind=='enum_type_extension':assign(node.name,'enum');features.add('extensions')
  elif kind=='enum_type_definition':assign(node.name,'enum','declaration');features.add('enums')
  elif kind=='enum_value_definition':assign(node.name,'enum-member','declaration')
  elif kind=='enum_value':assign(node,'enum-member');features.add('values')
  elif kind=='named_type':assign(node.name,'type',*(['default-library']if node.name.value in BUILTINS else []));features.add('types')
  elif kind=='operation_definition':assign(node.name,'function','declaration');features.add('operations')
  elif kind=='fragment_definition':assign(node.name,'label','declaration');features.add('fragments')
  elif kind=='fragment_spread':assign(node.name,'label');features.add('fragments')
  elif kind=='field':
   assign(node.name,'property');assign(node.alias,'property');features.add('fields')
   if node.alias:features.add('aliases')
  elif kind=='field_definition':assign(node.name,'property','declaration');features.add('schema')
  elif kind=='input_value_definition':assign(node.name,'parameter'if parent and parent.kind in {'field_definition','directive_definition'}else 'property','declaration')
  elif kind=='argument':assign(node.name,'parameter');features.add('arguments')
  elif kind=='variable':assign(node.name,'variable');features.add('variables')
  elif kind=='directive':assign(node.name,'decorator');features.add('directives')
  elif kind=='directive_definition':
   assign(node.name,'decorator','declaration')
   for location in node.locations:assign(location,'keyword')
   features.add('directives')
  elif kind in {'boolean_value','null_value'}:assign(node,'keyword');features.add('values')
  elif kind=='object_field':assign(node.name,'property');features.add('values')
  for child_key in node.keys:
   if child_key=='loc':continue
   child=getattr(node,child_key,None)
   if isinstance(child,(tuple,list)):
    for value in child:walk(value,node,child_key)
   elif isinstance(child,Node):walk(child,node,child_key)
 if ast:walk(ast)
 spans=[]
 def add(a,b,role,mods=()):
  if a>=b:return
  span=dict(start=units[a],end=units[b],tokenType=role)
  if mods:span['modifiers']=list(mods)
  spans.append(span)
 previous=0
 for token in tokens:
  # The reference lexer ignores BOM and insignificant commas. Preserve each as punctuation.
  for i in range(previous,token.start):
   if source[i]in ',\ufeff':add(i,i+1,'punctuation')
   elif not source[i].isspace():raise ValueError('Uncovered GraphQL source')
  k=token.kind
  if k==TokenKind.COMMENT:role,mods='comment',[];features.add('comments')
  elif k in {TokenKind.STRING,TokenKind.BLOCK_STRING}:role,mods='string',[];features.add('block-strings'if k==TokenKind.BLOCK_STRING else 'strings')
  elif k in {TokenKind.INT,TokenKind.FLOAT}:role,mods='number',[];features.add('numbers')
  elif k==TokenKind.NAME:
   role,mods=roles.get((token.start,token.end),('keyword',[]))
  else:role,mods=('operator'if k in {TokenKind.SPREAD,TokenKind.BANG,TokenKind.PIPE,TokenKind.AMP,TokenKind.DOLLAR,TokenKind.EQUALS,TokenKind.AT}else 'punctuation'),[]
  add(token.start,token.end,role,mods);previous=token.end
 for i in range(previous,len(source)):
  if source[i]in ',\ufeff':add(i,i+1,'punctuation')
  elif not source[i].isspace():raise ValueError('Uncovered GraphQL suffix')
 if '\r\n'in source:features.add('crlf')
 if any(ord(c)>127 for c in source):features.add('unicode')
 return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
