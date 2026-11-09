"""Capture bounded original local JDK sources and their complete license bundle."""
import hashlib
import json
from pathlib import Path
import zipfile

from packs.java.labeling.label import jdk_home
from packs.java.dataset.fetch_sources import write_original
from training.shared.spec import PackSpec, file_hash


def main():
    home = jdk_home()
    archive = home / 'lib/src.zip'
    root = PackSpec.open('java').dataset_root / 'sources/openjdk-22.0.1-local-v1'
    root.mkdir(parents=True, exist_ok=True)
    chosen, hashes = [], {}
    with zipfile.ZipFile(archive) as sources:
        for prefix, count in [('java.base/', 90), ('jdk.compiler/', 30), ('java.net.http/', 15), ('java.sql/', 10), ('java.logging/', 10)]:
            candidates = [x for x in sources.infolist() if x.filename.startswith(prefix) and x.filename.endswith('.java')
                          and 1500 < x.file_size <= 14000 and '/package-info.java' not in x.filename]
            candidates.sort(key=lambda x: hashlib.sha256(x.filename.encode()).hexdigest())
            for entry in candidates[:count]:
                raw = sources.read(entry)
                write_original(root, entry.filename, raw)
                hashes[entry.filename] = hashlib.sha256(raw).hexdigest()
                chosen.append(entry.filename)
    licenses = []
    for name in ('LICENSE', 'ADDITIONAL_LICENSE_INFO', 'ASSEMBLY_EXCEPTION'):
        raw = (home / 'legal/java.base' / name).read_bytes()
        write_original(root, name, raw)
        licenses.append(b'\n\n===== Original OpenJDK ' + name.encode() + b' =====\n' + raw)
    bundle = b''.join(licenses)
    write_original(root, 'LICENSES.txt', bundle)
    lock = {'format': 'nsh-java-jdk-capture-v1', 'jdkReleaseSha256': file_hash(home / 'release'),
            'sourceArchiveSha256': file_hash(archive), 'collectorHash': file_hash(Path(__file__)),
            'files': hashes, 'licenseSha256': hashlib.sha256(bundle).hexdigest()}
    target = root / 'source.lock.json'
    if target.exists() and json.loads(target.read_text()) != lock:
        raise ValueError('Preserve existing local JDK capture')
    target.write_text(json.dumps(lock, indent=2) + '\n')
    print('OpenJDK:', len(chosen), 'original Java files')


if __name__ == '__main__':
    main()
