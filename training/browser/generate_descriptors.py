"""Generate optional local descriptors and a weight-free, pinned asset catalog."""
from pathlib import Path
import argparse
import hashlib
import json

IDS = ['typescript', 'go', 'css', 'html', 'vue', 'python', 'bash', 'perl', 'awk',
       'sql', 'powershell', 'bat', 'assembly', 'java', 'csharp', 'c', 'cpp', 'php',
       'svelte', 'rust', 'zig', 'dart', 'swift', 'kotlin', 'r', 'scala', 'ruby',
       'lua', 'json', 'yaml', 'toml', 'ini', 'dotenv', 'xml', 'markdown',
       'dockerfile', 'makefile', 'graphql', 'protobuf', 'diff']
DEPENDENCIES = {'html': ['typescript', 'css'], 'vue': ['typescript', 'css'],
                'svelte': ['typescript', 'css'], 'php': ['html']}
ALIASES = {'patch': 'diff', 'proto': 'protobuf', 'flutter': 'dart', 'jsonc': 'json', 'svg': 'xml'}
LOCAL = Path('packages/models/src')
COMPAT = Path('packages/highlighter/src/languages')


def asset_record(pack_id):
    raw = (Path('packs') / pack_id / 'browser/model.json').read_bytes()
    metadata = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    return {
        'id': pack_id,
        'manifest': metadata['manifest'],
        'sha256': metadata['model']['sha256'],
        'bytes': metadata['model']['bytes'],
        'path': f"v1/{pack_id}/{metadata['model']['sha256']}.onnx",
        'metadata': {'sha256': digest, 'path': f'v1/{pack_id}/{digest}.json'},
        'dependencies': DEPENDENCIES.get(pack_id, []),
    }


def generate(pack_id):
    metadata = json.loads((Path('packs') / pack_id / 'browser/model.json').read_text())
    record = {'id': pack_id, 'manifest': metadata['manifest'], 'sha256': metadata['model']['sha256'],
              'contextBytes': metadata['contextBytes'], 'schema': metadata['schema'],
              'modifierThreshold': metadata['modifierThreshold'], 'decoder': metadata['decoder']}
    for key in ('inferenceWindowing', 'structuredDecoder'):
        if metadata.get(key) is not None:
            record[key] = metadata[key]
    text = 'import type { BrowserModel } from "@nsh/browser";\n'
    for dependency in DEPENDENCIES.get(pack_id, []):
        text += f'import {dependency} from "./{dependency}.js";\n'
    text += '\nconst model: BrowserModel = {\n' + json.dumps(record, indent=2)[2:-2]
    path = asset_record(pack_id)['path']
    text += f',\n  modelUrl: () => new URL("../assets/{path}", import.meta.url).href,\n'
    if pack_id in DEPENDENCIES:
        text += '  dependencies: [' + ', '.join(DEPENDENCIES[pack_id]) + '],\n'
    text += '};\nexport default model;\n'
    (LOCAL / 'languages' / (pack_id + '.ts')).write_text(text)
    (COMPAT / (pack_id + '.ts')).write_text(
        '/** Optional local assets; install @nsh/models to use this compatibility entry. */\n'
        f'export {{ default }} from "@nsh/models/languages/{pack_id}";\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', choices=IDS, help='Regenerate one descriptor and refresh the asset catalog')
    args = parser.parse_args()
    (LOCAL / 'languages').mkdir(parents=True, exist_ok=True)
    for pack_id in ([args.pack] if args.pack else IDS):
        generate(pack_id)
    # Pin decoder metadata as well as weights; no local ONNX URL/import here.
    records = [asset_record(pack_id) for pack_id in IDS]
    (LOCAL / 'asset-catalog.json').write_text(json.dumps(records, indent=2) + '\n')
    Path('packages/highlighter/src/model-assets.ts').write_text(
        'import type { PackManifest } from "@nsh/core";\n\n'
        'export interface ModelAsset {\n'
        '  id: string; manifest: PackManifest; sha256: string; bytes: number; path: string;\n'
        '  metadata: { sha256: string; path: string }; dependencies: readonly string[];\n'
        '}\n\n'
        'export const modelAssets: readonly ModelAsset[] = '
        + json.dumps(records, indent=2) + ';\n')
    if args.pack:
        return
    imports = ''.join(f'import {pack_id} from "./languages/{pack_id}.js";\n' for pack_id in IDS)
    (LOCAL / 'index.ts').write_text(imports + '\nexport const allModels = [' + ', '.join(IDS) + '] as const;\n')
    for alias, parent in ALIASES.items():
        (LOCAL / 'languages' / (alias + '.ts')).write_text(f'export {{ default }} from "./{parent}.js";\n')
        (COMPAT / (alias + '.ts')).write_text(f'export {{ default }} from "@nsh/models/languages/{alias}";\n')


if __name__ == '__main__':
    main()
