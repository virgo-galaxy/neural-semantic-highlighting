"""Capture bounded pinned java sources/licenses without builds or execution."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote
import hashlib
import json
import subprocess
import tarfile

from training.shared.spec import PackSpec, REPOSITORY, file_hash


def write_original(root, name, raw):
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Unsafe upstream source path')
    raw.decode('utf-8')
    if path.exists() and path.read_bytes() != raw:
        raise ValueError('Preserve previous java source capture: ' + name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(raw)


def main():
    spec = PackSpec.open('java')
    config = json.loads(Path(__file__).with_name('upstreams.json').read_text())
    for entry in config['upstreams']:
        root = spec.dataset_root / 'sources' / entry['id']
        root.mkdir(parents=True, exist_ok=True)
        files = {}
        if 'repository' in entry:
            def fetch(item):
                name = item['path']
                path = root / name
                if not path.resolve().is_relative_to(root.resolve()):
                    raise ValueError('Unsafe source path')
                url = f"https://raw.githubusercontent.com/{entry['repository']}/{entry['revision']}/{quote(name, safe='/')}"
                raw = path.read_bytes() if path.exists() else subprocess.check_output([
                    'curl', '--fail', '--silent', '--show-error', '--location', '--http1.1', '--retry', '3', '--retry-all-errors', url])
                blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
                if blob != item['gitBlob']:
                    raise ValueError('Pinned Git blob changed: ' + name)
                write_original(root, name, raw)
                return name, {'sha256': hashlib.sha256(raw).hexdigest(), 'gitBlob': blob, 'url': url}
            with ThreadPoolExecutor(max_workers=4) as pool:
                files.update(pool.map(fetch, entry['files']))
            # Retain each original license and one complete collector-facing bundle.
            combined = b''.join(b'\n\n===== Original upstream: ' + item['path'].encode() + b' =====\n' +
                                (root / item['path']).read_bytes() for item in entry['files'] if item['license'])
            write_original(root, 'LICENSES.txt', combined)
            files['LICENSES.txt'] = {'sha256': hashlib.sha256(combined).hexdigest()}
        else:
            archive = REPOSITORY / 'artifacts/tools/java-metadata' / entry['url'].rsplit('/', 1)[-1]
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                raw = subprocess.check_output(['curl', '--fail', '--silent', '--show-error', '--location', entry['url']])
                if hashlib.sha256(raw).hexdigest() != entry['archiveSha256']:
                    raise ValueError('Official archive hash changed')
                archive.write_bytes(raw)
            if file_hash(archive) != entry['archiveSha256']:
                raise ValueError('Cached official archive differs')
            with tarfile.open(archive) as bundle:
                for item in entry['files']:
                    member = bundle.getmember(entry['archivePrefix'] + item['path'])
                    if not member.isfile():
                        raise ValueError('Expected an original source file')
                    raw = bundle.extractfile(member).read()
                    if hashlib.sha256(raw).hexdigest() != item['sha256']:
                        raise ValueError('Pinned archive member differs')
                    write_original(root, item['path'], raw)
                    files[item['path']] = {'sha256': item['sha256'], 'archiveSha256': entry['archiveSha256']}
        lock = {'format': 'nsh-java-source-lock-v1', 'upstream': entry,
                'collectorHash': file_hash(Path(__file__)), 'files': files}
        path = root / 'source.lock.json'
        if path.exists() and json.loads(path.read_text()) != lock:
            raise ValueError('Preserve previous java capture lock')
        path.write_text(json.dumps(lock, indent=2) + '\n')
        print(entry['id'], sum(not item['license'] for item in entry['files']), 'java source files')


if __name__ == '__main__':
    main()
