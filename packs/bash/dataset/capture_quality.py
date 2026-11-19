"""Freeze additional installed Zsh function families without executing shell code."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shutil

from training.shared.spec import PackSpec, file_hash


def main():
    spec = PackSpec.open('bash')
    config = spec.directory / 'dataset'
    history = config / 'history/pre-quality-20261119'
    history.mkdir(parents=True, exist_ok=True)
    for name in ['sources.json', 'split-groups.json']:
        target = history / name
        if not target.exists():
            shutil.copyfile(config / name, target)
    sources = json.loads((history / 'sources.json').read_text())
    groups = json.loads((history / 'split-groups.json').read_text())
    seen = {Path(name).name for entry in sources['sources'] for name in entry.get('files', [])}
    origin = Path('/usr/share/zsh/5.9/functions')
    families = defaultdict(list)
    for path in origin.iterdir():
        if not path.is_file() or not 300 < path.stat().st_size < 18000:
            continue
        if any(path.name == name or path.name.startswith(name + '-') for name in seen):
            continue
        family = path.name.lstrip('_').split('_')[0].split('-')[0]
        families[family].append(path.name)
    chosen, mapping, folds = [], {}, {}
    for family, names in sorted(families.items(), key=lambda item: hashlib.sha256(item[0].encode()).hexdigest()):
        if len(chosen) >= 96:
            break
        selected = sorted(names, key=lambda name: hashlib.sha256(name.encode()).hexdigest())[:3]
        key = 'zsh-installed-5.9-quality:' + family
        bucket = int(hashlib.sha256(('quality-shell:' + family).encode()).hexdigest()[:8], 16) % 10
        split = 'validation' if bucket == 0 else 'test' if bucket == 1 else 'train'
        groups['assignments'][key] = split
        folds[key] = split
        chosen.extend(selected)
        mapping.update({name: family for name in selected})
    protocol = dict(format='nsh-shell-quality-protocol-v1', origin=str(origin), files=chosen, folds=folds,
        policy='Metadata-selected installed Zsh 5.9 functions; original named families excluded; no source execution or SDK installation',
        freshTestSourceGroups=[name for name, split in folds.items() if split == 'test'])
    target = config / 'quality-protocol.json'
    if target.exists() and json.loads(target.read_text()) != protocol:
        raise ValueError('Preserve frozen Shell protocol')
    target.write_text(json.dumps(protocol, indent=2) + '\n')
    folder = spec.dataset_root / 'sources/zsh-quality-20261119'
    hashes = {}
    for name in chosen:
        raw = (origin / name).read_bytes()
        raw.decode('utf-8')
        target = folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != raw:
            raise ValueError('Preserve installed source capture')
        if not target.exists():
            target.write_bytes(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    raw = (spec.dataset_root / 'sources/zsh-5.9/LICENCE').read_bytes()
    target = folder / 'LICENCE'
    if target.exists() and target.read_bytes() != raw:
        raise ValueError('Preserve upstream license')
    if not target.exists():
        target.write_bytes(raw)
    hashes['LICENCE'] = hashlib.sha256(raw).hexdigest()
    lock = dict(origin=str(origin), collectorHash=file_hash(Path(__file__)), files=hashes,
                license='Complete original Zsh 5.9 upstream LICENCE; per-file notices preserved')
    target = folder / 'source.lock.json'
    if target.exists() and json.loads(target.read_text()) != lock:
        raise ValueError('Preserve source lock')
    if not target.exists():
        target.write_text(json.dumps(lock, indent=2) + '\n')
    sources['sources'].append(dict(id='zsh-installed-5.9-quality', base='dataset', path='bash/sources/zsh-quality-20261119',
        profile='zsh', extensions=[''], files=chosen, groups=mapping, maxBytes=18000,
        license='bash/sources/zsh-quality-20261119/LICENCE'))
    for name, data in [('sources', sources), ('split-groups', groups)]:
        (config / (name + '.json')).write_text(json.dumps(data, indent=2) + '\n')
    print(len(chosen), 'installed Zsh source files captured without execution')


if __name__ == '__main__':
    main()
