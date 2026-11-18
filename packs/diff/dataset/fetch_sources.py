"""Capture a bounded immutable Diff/Patch corpus and original licenses; never build it."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote
import hashlib
import json
import subprocess
from training.shared.spec import PackSpec, file_hash, REPOSITORY


def main():
    spec = PackSpec.open('diff')
    config = json.loads(Path(__file__).with_name('upstreams.json').read_text())
    def write(path, raw):
        raw.decode('utf-8')
        if path.exists() and path.read_bytes() != raw: raise ValueError('Preserve previous Diff/Patch capture: ' + str(path))
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists(): path.write_bytes(raw)
    for entry in config['upstreams']:
        root = spec.dataset_root / 'sources' / entry['id']
        def fetch(item):
            name = item['path']; path = root / name
            if not path.resolve().is_relative_to(root.resolve()): raise ValueError('Unsafe upstream source path')
            url = f"https://raw.githubusercontent.com/{entry['repository']}/{entry['revision']}/{quote(name, safe='/')}"
            cache = REPOSITORY / 'artifacts/diff/capture-cache' / entry['id'] / name
            raw = path.read_bytes() if path.exists() else cache.read_bytes() if cache.exists() else subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--http1.1','--retry','3','--retry-all-errors',url])
            blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            if blob != item['gitBlob']: raise ValueError('Pinned Git blob changed: ' + name)
            write(path, raw)
            return name, {'sha256': hashlib.sha256(raw).hexdigest(), 'gitBlob': blob, 'url': url}
        with ThreadPoolExecutor(max_workers=4) as pool: files = dict(pool.map(fetch, entry['files']))
        combined = b''.join(b'\n\n===== Original upstream: ' + item['path'].encode() + b' =====\n' + (root / item['path']).read_bytes() for item in entry['files'] if item['license'])
        write(root / 'LICENSES.txt', combined)
        files['LICENSES.txt'] = {'sha256': hashlib.sha256(combined).hexdigest()}
        lock = {'format':'nsh-diff-source-lock-v1','upstream':entry,'collectorHash':file_hash(Path(__file__)),'files':files}
        path = root / 'source.lock.json'
        if path.exists() and json.loads(path.read_text()) != lock: raise ValueError('Preserve previous Diff/Patch capture lock')
        path.write_text(json.dumps(lock,indent=2)+'\n')
        print(entry['id'],sum(not x['license'] for x in entry['files']),'original Diff/Patch files',flush=True)

if __name__ == '__main__': main()
