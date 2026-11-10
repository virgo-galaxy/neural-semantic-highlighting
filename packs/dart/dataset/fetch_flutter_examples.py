"""Capture pinned Flutter application review source only; never build or execute."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote
import hashlib,json,subprocess
from training.shared.spec import PackSpec,file_hash
from .fetch_sources import write_original

CONFIG=Path(__file__).with_name('flutter-examples.json')
def main():
    config=json.loads(CONFIG.read_text())
    root=PackSpec.open('dart').dataset_root/'sources'/config['id'];root.mkdir(parents=True,exist_ok=True)
    def fetch(item):
        name=item['path'];path=root/name
        if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe Flutter source path')
        url=f"https://raw.githubusercontent.com/{config['repository']}/{config['revision']}/{quote(name,safe='/')}"
        raw=path.read_bytes() if path.exists() else subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--http1.1','--retry','3','--retry-all-errors',url])
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob!=item['gitBlob']:raise ValueError('Pinned Flutter source differs: '+name)
        write_original(root,name,raw)
        return name,dict(sha256=hashlib.sha256(raw).hexdigest(),gitBlob=blob,url=url)
    with ThreadPoolExecutor(max_workers=4) as pool:files=dict(pool.map(fetch,config['files']))
    lock=dict(format='nsh-flutter-review-source-lock-v1',upstream=config,collectorHash=file_hash(Path(__file__)),files=files)
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Preserve original Flutter review capture')
    path.write_text(json.dumps(lock,indent=2)+'\n')
    print(sum(not x['license'] for x in config['files']),'Flutter review files:',root)
if __name__=='__main__':main()
