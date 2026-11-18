"""Original unified-patch structural families, independent of Golden and displays."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash
WORDS='acorn birch coral dune elm fern grove heath isle juniper kelp larch maple north oak pine quartz reed sage thyme'.split()
def unified(path,old,new,context=(),suffix='',git=False):
 old_lines=list(context)+list(old);new_lines=list(context)+list(new)
 header=(f'diff --git a/{path} b/{path}\nindex 1234567..abcdef0 100644\n'if git else '')+f'--- a/{path}\n+++ b/{path}\n@@ -1,{len(old_lines)} +1,{len(new_lines)} @@'+suffix+'\n'
 return header+''.join(' '+s+'\n'for s in context)+''.join('-'+s+'\n'for s in old)+''.join('+'+s+'\n'for s in new)
def task(f,w,v):
 n=v+2;path=w+'/source.txt'
 if f=='js':return unified(w+'/app.ts',[f'const {w} = {n};'],[f'export const {w} = {n+1};'],['// Shared application'],git=True)
 if f=='python':return unified(w+'/main.py',['def run():',f'    return "{w}"'],['def run(value):',f'    return value or "{w}"'],suffix=' def run')
 if f=='go':return unified(w+'/main.go',['func Count() int {',f'    return {n}','}'],['func Count() int {',f'    return {n+1}','}'],git=True)
 if f=='css':return unified(w+'/theme.css',[f'.{w} {{ color: red; }}'],[f'.{w} {{ color: green; padding: {n}px; }}'],['/* Shared style */'])
 if f=='html':return unified(w+'/index.html',['<main>Old</main>'],[f'<main class="{w}">New</main>'],git=True)
 if f=='json':return unified(w+'/package.json',[f'  "name": "old-{w}",'],[f'  "name": "new-{w}",'],['{'],git=True)
 if f=='shell':return unified(w+'/build.sh',['set -e',f'echo "{w}"'],['set -eu',f'printf "%s\\n" "{w}"'],['#!/bin/sh'])
 if f=='make':return unified(w+'/Makefile',[f'\tcc -o {w} main.c'],[f'\t$(CC) -Wall -o {w} main.c'],['all:'],git=True)
 if f=='new':return f'diff --git a/{w}.txt b/{w}.txt\nnew file mode 100644\n--- /dev/null\n+++ b/{w}.txt\n@@ -0,0 +1,2 @@\n+Created {w}\n+Revision {n}\n'
 if f=='delete':return f'diff --git a/{w}.txt b/{w}.txt\ndeleted file mode 100644\n--- a/{w}.txt\n+++ /dev/null\n@@ -1,2 +0,0 @@\n-Original {w}\n-Revision {n}\n'
 if f=='rename':return f'diff --git a/old-{w} b/new-{w}\nsimilarity index 100%\nrename from old-{w}\nrename to new-{w}\n'
 if f=='copy':return f'diff --git a/{w}.txt b/copy-{w}.txt\nsimilarity index 100%\ncopy from {w}.txt\ncopy to copy-{w}.txt\n'
 if f=='mode':return f'diff --git a/{w}.sh b/{w}.sh\nold mode 100644\nnew mode 100755\n'
 if f=='mail':return f'From {v:040x} Mon Sep 17 00:00:00 2001\nFrom: Original Author <author@example.test>\nDate: Thu, 19 Nov 2026 01:00:00 +0800\nSubject: [PATCH] Improve {w}\n\nAn original description for {w}, revision {n}.\n\n---\n file | 2 +-\n 1 file changed, 1 insertion(+), 1 deletion(-)\n\n'+unified(w+'/file',['old '+w],['new '+w],git=True)+'-- \n2.39.5\n'
 if f=='no-eol':return f'--- a/{w}\n+++ b/{w}\n@@ -1 +1 @@\n-old {w}\n\\ No newline at end of file\n+new {w}\n\\ No newline at end of file\n'
 if f=='multi-hunk':return unified(w+'/file',['old '+w],['new '+w],git=True)+f'@@ -{n+10} +{n+10} @@ helper\n-second {w}\n+last {w}\n'
 if f=='multi-file':return unified(w+'/first',['first '+w],['next '+w],git=True)+unified(w+'/second',['second '+w],['last '+w],git=True)
 if f=='header-shaped':return unified(w+'/header',['--- '+w,'@@ -2 +2 @@'],['+++ '+w,'diff --git a/x b/x'],git=True)
 if f=='unicode':return unified(w+'/notes',['旧的 '+w+' 🌌'],['新的 '+w+' 👩🏽‍💻'],['// 原始文本'])
 if f=='separators':return unified(w+'/notes',[w+'\u2028original'],[w+'\u2029updated'])
 if f=='blank':return unified(w+'/blank',['',w],['',w+' updated'],[''])
 if f=='whitespace':return unified(w+'/spacing',['\t'+w+'  '],['  '+w+'\t'],['\t'])
 if f=='quoted-path':return f'diff --git "a/{w} name" "b/{w} name"\n--- "a/{w} name"\n+++ "b/{w} name"\n@@ -1 +1 @@\n-old {w}\n+new {w}\n'
 if f=='null-marker':return unified(w+'/logic',['--- /dev/null','-- signature'],['+++ /dev/null','++ prefix'],git=True)
 if f=='long-added':return unified(w+'/long',['short '+w],[('Original '+w+' 🌌 with spaces, + and - markers. ')*30])
 if f=='long-deleted':return unified(w+'/long',[('Previous '+w+' text with <script> and 🌌. ')*30],['short '+w])
 if f=='long-context':return unified(w+'/long',['old '+w],['new '+w],[('Shared '+w+' text 🌌 with braces {}. ')*28])
 if f=='long-preamble':return ('An original '+w+' change description with + and - signs. ')*32+'\n\n'+unified(w+'/file',['old '+w],['new '+w],git=True)
 if f=='many-context':return unified(w+'/list',['old '+w],['new '+w],[f'context {w} {i}'for i in range(35)],git=True)
 if f=='binary':return f'diff --git a/{w}.png b/{w}.png\nBinary files a/{w}.png and b/{w}.png differ\n'
 if f=='fragment':return f'-original {w} = {n}\n+updated {w} = {n+1}\n context {w}\n'
 if f=='index':return f'Index: source/{w}\n'+('='*67)+'\n'+unified(w+'/source',['old '+w],['new '+w])
 if f=='bom':return '\ufeff'+unified(w+'/text',['old '+w],['new '+w])
 raise ValueError(f)
FAMILIES='js python go css html json shell make new delete rename copy mode mail no-eol multi-hunk multi-file header-shaped unicode separators blank whitespace quoted-path null-marker long-added long-deleted long-context long-preamble many-context binary fragment index bom'.split()
def main():
 root=PackSpec.open('diff').dataset_root/'sources/curriculum-v1';files={}
 for i,family in enumerate(FAMILIES):
  for v in range(20):
   w=WORDS[(i+v)%len(WORDS)];source=task(family,w,v)
   if v%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();p=root/family/f'{v:02}.diff';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve previous task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original Diff/Patch tasks authored for Neural Semantic Highlighting.\nPrivate development data; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve original license')
 p.write_bytes(license);lock=dict(format='nsh-diff-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(FAMILIES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'original Diff tasks')
if __name__=='__main__':main()
