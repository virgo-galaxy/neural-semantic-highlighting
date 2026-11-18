"""Offline unified/Git patch line roles with independent parse-only Git validation."""
import re
from .tools import provenance,statistics
HUNK=re.compile(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)\Z')
GIT_META=('index ','new file mode ','deleted file mode ','old mode ','new mode ','similarity index ','dissimilarity index ','rename from ','rename to ','copy from ','copy to ','Binary files ','GIT binary patch','literal ','delta ')
MAIL_META=('From: ','Date: ','Subject: ','MIME-Version: ','Content-Type: ','Content-Transfer-Encoding: ','Message-Id: ','Message-ID: ','In-Reply-To: ','References: ')
def label(*,source,document_kind='diff',profile=None):
 if not isinstance(source,str)or document_kind!='diff'or(profile or document_kind)!='diff':raise ValueError('Expected matching Diff kind/profile')
 source.encode();provenance()
 if '\x00'in source or '\r'in source.replace('\r\n',''):raise ValueError('Unsupported patch control or bare CR')
 if source.startswith('\x1b')or'\x1b['in source:raise ValueError('ANSI-colored patches are outside this source contract')
 units=[0]
 for c in source:units.append(units[-1]+len(c.encode('utf-16-le'))//2)
 spans=[];features=set();offset=0;lines=[];bom=source.startswith('\ufeff');text=source[1:]if bom else source
 physical_lines=text.split('\n')
 for i,physical in enumerate(physical_lines):
  content=physical[:-1]if physical.endswith('\r')else physical;lines.append((offset+int(bom),content));offset+=len(physical)+(i<len(physical_lines)-1)
 def add(a,b,role):
  if b>a:spans.append(dict(start=units[a],end=units[b],tokenType=role))
 if bom:add(0,1,'punctuation');features.add('bom')
 # Headerless +/- snippets are accepted as editor fragments, not complete patch proofs.
 full=any(s.startswith(('diff --git ','diff -','--- ','@@ '))for _,s in lines)
 fragment=not full and any(s.startswith(('+','-'))for _,s in lines)and all(not s or s.startswith(('+','-',' ','\\ No newline'))for _,s in lines)
 old_left=new_left=0;hunks=0;added=deleted=0;binary=False;file_pair=False
 for index,(a,line)in enumerate(lines):
  if old_left or new_left:
   if line.startswith('\\ No newline at end of file'):role='comment';features.add('no-newline')
   elif line.startswith('+'):
    if new_left<1:raise ValueError('Too many added patch lines')
    role='addition';new_left-=1;added+=1;features.add('additions')
   elif line.startswith('-'):
    if old_left<1:raise ValueError('Too many removed patch lines')
    role='deletion';old_left-=1;deleted+=1;features.add('deletions')
   elif line.startswith(' '):
    if min(old_left,new_left)<1:raise ValueError('Patch context exceeds hunk range')
    role='text';old_left-=1;new_left-=1;features.add('context')
   else:raise ValueError('Incomplete unified hunk or invalid line prefix')
  elif line.startswith('diff --cc ')or line.startswith('diff --combined ')or line.startswith('@@@'):
   raise ValueError('Combined merge diffs are outside the unified baseline')
  elif line.startswith(('diff --git ','diff -')):role='heading';binary=False;file_pair=False;features.add('git-headers')
  elif line.startswith('--- ')and index+1<len(lines)and lines[index+1][1].startswith('+++ '):role='heading';file_pair=True;features.add('file-headers')
  elif file_pair and line.startswith('+++ '):role='heading'
  elif line.startswith('@@ '):
   m=HUNK.fullmatch(line)
   if not m:raise ValueError('Invalid unified hunk header')
   old_left=int(m[2])if m[2]is not None else 1;new_left=int(m[4])if m[4]is not None else 1;hunks+=1;role='label';features.add('hunks')
  elif line.startswith('\\ No newline at end of file'):role='comment';features.add('no-newline')
  elif line.startswith(GIT_META):
   role='comment';features.add('metadata')
   if line.startswith(('GIT binary patch','Binary files ')):binary=True;features.add('binary')
   if line.startswith(('rename ','copy ','similarity ','dissimilarity ')):features.add('renames-copies')
  elif binary:role='comment'
  elif line.startswith('Index: '):role='heading';features.add('index-headers')
  elif line.startswith(MAIL_META)or re.fullmatch(r'From [0-9a-f]{40,64} Mon Sep 17 00:00:00 2001',line)or line in {'---','-- '}or(line.startswith('=')and set(line)=={'='}):role='comment';features.add('mail-metadata')
  elif fragment:
   role='addition'if line.startswith('+')else 'deletion'if line.startswith('-')else 'text';features.add('fragments')
   if role=='addition':features.add('additions')
   if role=='deletion':features.add('deletions')
  else:role='text'
  add(a,a+len(line),role)
 if old_left or new_left:raise ValueError('Incomplete unified hunk counts')
 if full:
  parsed=statistics(text);rows=[r.split(b'\t',2)for r in parsed.split(b'\0')if r]
  if hunks and not rows:raise ValueError('No unified patch recognized by independent Git parser')
  numeric=[r for r in rows if len(r)==3 and r[0].isdigit()and r[1].isdigit()]
  if (sum(int(r[0])for r in numeric),sum(int(r[1])for r in numeric))!=(added,deleted):raise ValueError('Original hunk counts disagree with independent Git parse')
  features.add('complete-patch')
 if '\r\n'in source:features.add('crlf')
 if any(ord(c)>127 for c in source):features.add('unicode')
 return dict(offsetEncoding='utf-16',spans=spans,features=sorted(features))
