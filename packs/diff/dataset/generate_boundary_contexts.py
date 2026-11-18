"""Original coverage for no-newline markers and rename paths, not display copies."""
from pathlib import Path
import json,hashlib
from training.shared.spec import PackSpec,file_hash
from .generate_curriculum import WORDS,unified
KINDS=['replace','insert','delete','context','multiple','metadata','rename-source','rename-script']
def main():
 root=PackSpec.open('diff').dataset_root/'sources/curriculum-boundaries-v1';files={}
 for kind in KINDS:
  for v in range(20):
   w=WORDS[v%len(WORDS)];path=kind+'/'+w+'/value.txt';old='Previous '+kind+' '+w;new='Updated '+kind+' '+w
   if kind.startswith('rename-'):
    ext='ts'if kind=='rename-source'else'sh';a=f'src/{w}/old.{ext}';b=f'src/{w}/new.{ext}';source=f'diff --git a/{a} b/{b}\nsimilarity index 80%\nrename from {a}\nrename to {b}\n--- a/{a}\n+++ b/{b}\n@@ -1 +1 @@\n-'+old+'\n+'+new+'\n'
   else:
    header=f'--- a/{path}\n+++ b/{path}\n'
    if kind=='insert':source=header+'@@ -0,0 +1 @@\n+'+new+'\n\\ No newline at end of file\n'
    elif kind=='delete':source=header+'@@ -1 +0,0 @@\n-'+old+'\n\\ No newline at end of file\n'
    elif kind=='context':source=header+'@@ -1,2 +1,2 @@\n Shared '+kind+' '+w+'\n-'+old+'\n\\ No newline at end of file\n+'+new+'\n\\ No newline at end of file\n'
    else:source=header+'@@ -1 +1 @@\n-'+old+'\n\\ No newline at end of file\n+'+new+'\n\\ No newline at end of file\n'
    if kind=='multiple':source+=unified(w+'/extra.txt',['Old extra '+w],['New extra '+w],git=True)
    if kind=='metadata':source=f'diff --git a/{path} b/{path}\nindex 1234567..abcdef0 100644\n'+source
   if v%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();p=root/kind/f'{v:02}.diff';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve boundary task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original Diff boundary tasks for Neural Semantic Highlighting.\nNo upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve license')
 p.write_bytes(license);lock=dict(format='nsh-diff-boundary-curriculum-v1',generatorSha256=file_hash(Path(__file__)),baseGeneratorSha256=file_hash(Path(__file__).with_name('generate_curriculum.py')),families=len(KINDS),files=files);p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve boundary lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'original boundary contexts')
if __name__=='__main__':main()
