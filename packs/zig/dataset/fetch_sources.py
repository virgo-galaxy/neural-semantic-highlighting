"""Capture only pinned official Zig 0.17.1 std/compiler source; never build it."""
from pathlib import Path
import hashlib,json,subprocess,tarfile
from training.shared.spec import PackSpec,REPOSITORY,file_hash

def write_original(root,name,raw):
 p=root/name
 if not p.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe Zig source path')
 raw.decode('utf-8')
 if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve prior Zig source bytes')
 p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():p.write_bytes(raw)

def main():
 config=json.loads(Path(__file__).with_name('upstreams.json').read_text());spec=PackSpec.open('zig');archive=REPOSITORY/'artifacts/cache/zig/zig-0.17.1.tar.xz'
 if not archive.exists():
  archive.parent.mkdir(parents=True,exist_ok=True);data=subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--http1.1',config['upstreams'][0]['url']]);archive.write_bytes(data)
 for entry in config['upstreams']:
  if file_hash(archive)!=entry['archiveSha256']:raise ValueError('Official Zig 0.17.1 archive hash differs')
  root=spec.dataset_root/'sources'/entry['id'];files={}
  with tarfile.open(archive) as t:
   for item in entry['files']:
    member=t.getmember(entry['archivePrefix']+item['path'])
    if not member.isfile():raise ValueError('Expected original source file')
    raw=t.extractfile(member).read()
    if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Zig release source changed')
    write_original(root,item['path'],raw);files[item['path']]=item['sha256']
  lock=dict(format='nsh-zig-0.17.1-source-lock-v1',upstream=entry,collectorSha256=file_hash(Path(__file__)),files=files);p=root/'source.lock.json'
  if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve existing Zig source lock')
  p.write_text(json.dumps(lock,indent=2)+'\n');print(entry['id'],len(files)-1,'original source files')
if __name__=='__main__':main()
