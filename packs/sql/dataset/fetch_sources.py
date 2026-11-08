"""Fetch only selected pinned upstream SQL/license files; never execute scripts."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,subprocess
from urllib.parse import quote
from training.shared.spec import PackSpec,file_hash

def main():
    spec=PackSpec.open('sql');config=json.loads(Path(__file__).with_name('upstreams.json').read_text())
    for entry in config['upstreams']:
        root=spec.dataset_root/'sources'/entry['id'];root.mkdir(parents=True,exist_ok=True)
        def fetch(item):
            name=item['path'];path=root/name
            if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe upstream path')
            url=f"https://raw.githubusercontent.com/{entry['repository']}/{entry['revision']}/{quote(name,safe='/')}"
            raw=path.read_bytes() if path.exists() else subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--retry','2',url])
            expected=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if expected!=item['gitBlob']:raise ValueError('Pinned upstream Git blob differs: '+name)
            raw.decode('utf-8');path.parent.mkdir(parents=True,exist_ok=True)
            if not path.exists():path.write_bytes(raw)
            return name,{'sha256':hashlib.sha256(raw).hexdigest(),'gitBlob':expected,'bytes':len(raw),'url':url}
        files=dict(ThreadPoolExecutor(max_workers=8).map(fetch,entry['files']))
        lock={'format':'nsh-sql-upstream-source-v1','repository':entry['repository'],'revision':entry['revision'],'collectorHash':file_hash(Path(__file__)),'files':files}
        path=root/'source.lock.json'
        if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Preserve old SQL source capture')
        path.write_text(json.dumps(lock,indent=2)+'\n');print(entry['id'],len(files)-1,'SQL source files')

if __name__=='__main__':main()
