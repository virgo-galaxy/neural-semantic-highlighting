"""Fetch only selected pinned upstream BAT/CMD/license files; never execute scripts."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,subprocess
from urllib.parse import quote
from training.shared.spec import PackSpec,file_hash

def main():
    spec=PackSpec.open('bat');config=json.loads(Path(__file__).with_name('upstreams.json').read_text())
    for entry in config['upstreams']:
        root=spec.dataset_root/'sources'/entry['id'];root.mkdir(parents=True,exist_ok=True)
        def fetch(item):
            name=item['path'];path=root/name
            if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe upstream path')
            url=f"https://raw.githubusercontent.com/{entry['repository']}/{entry['revision']}/{quote(name,safe='/')}"
            raw=path.read_bytes() if path.exists() else subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--http1.1','--retry','3','--retry-all-errors','--connect-timeout','15','--max-time','90',url])
            expected=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if expected!=item['gitBlob']:raise ValueError('Pinned upstream Git blob differs: '+name)
            raw.decode(entry.get('encodings',{}).get(name,'utf-8'));path.parent.mkdir(parents=True,exist_ok=True)
            if not path.exists():path.write_bytes(raw)
            return name,{'sha256':hashlib.sha256(raw).hexdigest(),'gitBlob':expected,'bytes':len(raw),'url':url}
        files=dict(ThreadPoolExecutor(max_workers=8).map(fetch,entry['files']))
        # Preserve the original license bytes; the collector reads an explicitly
        # declared UTF-8 transcription for legacy-encoded legal text only.
        for name,encoding in entry.get('encodings',{}).items():
            item=next(x for x in entry['files'] if x['path']==name)
            if not item.get('license'):raise ValueError('Never transcode source code')
            raw=(root/name).read_bytes().decode(encoding).encode('utf-8');target=root/(name+'.utf8.txt')
            if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve license transcription')
            if not target.exists():target.write_bytes(raw)
            files[name+'.utf8.txt']={'sha256':hashlib.sha256(raw).hexdigest(),'sourceFile':name,'sourceEncoding':encoding,'bytes':len(raw)}
        lock={'format':'nsh-bat-upstream-source-v1','repository':entry['repository'],'revision':entry['revision'],'collectorHash':file_hash(Path(__file__)),'files':files}
        path=root/'source.lock.json'
        if path.exists():
            original=json.loads(path.read_text())
            if {k:v for k,v in original.items() if k!='collectorHash'}!={k:v for k,v in lock.items() if k!='collectorHash'}:raise ValueError('Preserve old BAT/CMD source capture')
        else:path.write_text(json.dumps(lock,indent=2)+'\n')
        print(entry['id'],len(files)-1,'BAT/CMD source files')

if __name__=='__main__':main()
