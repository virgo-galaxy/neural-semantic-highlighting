"""Original opaque multiline fence tasks; no Golden, display or test inputs."""
from pathlib import Path
import hashlib
import json
import random

from training.shared.spec import PackSpec, file_hash

BODIES = [
    ('python', 'import collections\nfrom decimal import Decimal\n\nrecords = [Decimal("@N@"), Decimal("2")]\n\nfor record in records:\n    print(record * 3)\n'),
    ('python', 'from dataclasses import dataclass\n\n\n@dataclass\nclass Entry:\n    name: str\n    quantity: int = @N@\n\nentries = [Entry("@W@")]\nprint(entries)\n'),
    ('text-archive', 'Archived @W@ material is ordinary source here.\nA second line contains words and punctuation.\n\nAnother paragraph is still part of the fenced body.\n\nThere are @N@ records in this source.\n'),
    ('unknown-notes', '保留 @W@ 的原始内容。第一行也属于代码区域。\n这里有中文、数字 @N@ 和星空 🌌。\n\n第二段不会结束这个围栏。\n# This is body text, including the hash.\n'),
    ('bash', 'set -eu\n\nname="@W@"\n\ncat <<DOCUMENT\nA literal line for ${name}.\n\nAnother line remains in the here document.\nDOCUMENT\nprintf "%s\\n" "$name"\n'),
    ('js', 'import { readFile } from "node:fs/promises";\n\nconst @W@ = await readFile("./notes", "utf8");\n\n// Source comments and blank lines stay inside this body.\nconsole.log(`value: ${@W@}`, @N@);\n'),
    ('config-fragment', '[source]\nname = "@W@"\n\n[values]\ncount = @N@\nready = true\n\n<!-- The angle brackets are also source. -->\n'),
    ('go', 'package source\n\nimport "fmt"\n\nfunc report() {\n\n    fmt.Println("@W@", @N@)\n}\n'),
]


def main():
    from packs.markdown.labeling.label import label
    root = PackSpec.open('markdown').dataset_root / 'sources/fences-v2'
    files = {}
    words = 'cobalt maple lotus garnet zephyr coral acorn sienna'.split()
    for blocks in range(1, 9):
        for variant in range(24):
            rng = random.Random(170317 + blocks * 97 + variant)
            word, number = words[variant % len(words)], str(rng.randrange(13, 180))
            parts = ['# Opaque source collection', '', '> The following samples are retained as source.', '',
                     '[Source reference](https://example.test/archive/' + word + ')', '']
            for block in range(blocks):
                language, body = BODIES[(variant + block) % len(BODIES)]
                body = body.replace('@W@', word).replace('@N@', number)
                fence = ('~' if variant % 4 == 1 else '`') * (3 + variant % 3)
                info = language + (' title=original.source' if variant % 5 == 0 else '')
                parts += ['### Retained sample ' + str(block + 1), '', 'The `source` below stays intact.', '',
                          fence + info, body.rstrip('\n'), fence, '', '**Review** the original source before continuing.', '']
            source = '\n'.join(parts)
            if variant % 4 == 3: source = source.replace('\n', '\r\n')
            if variant % 11 == 2: source = '\ufeff' + source
            label(source=source)
            raw = source.encode('utf-8')
            path = root / ('blocks-' + str(blocks)) / f'{variant:02}.md'
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.read_bytes() != raw:
                raise ValueError('Preserve original multiline fence task')
            if not path.exists(): path.write_bytes(raw)
            files[str(path.relative_to(root))] = hashlib.sha256(raw).hexdigest()
    license_bytes = b'Original multiline Markdown fence tasks for Neural Semantic Highlighting.\nPrivate development data; no upstream, Golden, display or held-out copies.\n'
    path = root / 'LICENSE'
    if path.exists() and path.read_bytes() != license_bytes: raise ValueError('Preserve fence license')
    path.write_bytes(license_bytes)
    lock = dict(format='nsh-markdown-fences-v2', generatorSha256=file_hash(Path(__file__)), families=8,
                files=files, licenseSha256=hashlib.sha256(license_bytes).hexdigest())
    path = root / 'source.lock.json'
    if path.exists() and json.loads(path.read_text()) != lock: raise ValueError('Preserve fence lock')
    path.write_text(json.dumps(lock, indent=2) + '\n')
    print(len(files), 'original multiline fence tasks in eight train-only structural families')


if __name__ == '__main__': main()
