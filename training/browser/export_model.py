"""Export a selected inference artifact to ONNX without training/quantization."""
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import sys

import numpy as np
import onnx
import onnxruntime as ort
import torch
from training.browser.model import BrowserTransformer

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def open_pack(pack_id):
    if pack_id == 'typescript':
        from packs.typescript.runtime.local import TypeScriptLocalPack
        return TypeScriptLocalPack(device=torch.device('cpu'))
    if pack_id in {'go', 'css', 'html', 'vue'}:
        classes = {'go': 'GoLocalPack', 'css': 'CssLocalPack', 'html': 'HtmlLocalPack', 'vue': 'VueLocalPack'}
        module = importlib.import_module(f'packs.{pack_id}.runtime.local')
        return getattr(module, classes[pack_id])(device_name='cpu')
    from training.shared.runtime import LocalPack
    return LocalPack(pack_id=pack_id, device_name='cpu')


def export(pack_id, output):
    source = ROOT / 'packs' / pack_id / 'model/model.pt'
    source_hash = digest(source)
    if output.exists():
        raise ValueError('Preserve existing browser export; choose a new target')
    output.mkdir(parents=True)
    torch.set_num_threads(4)
    torch.manual_seed(1729)
    pack = open_pack(pack_id)
    model = BrowserTransformer(pack.model).eval()
    metadata = json.loads((source.parent / 'model.json').read_text())
    if pack_id == 'typescript':
        schema = {'tokenTypes': list(pack.token_types), 'modifiers': list(pack.modifiers)}
        threshold = pack.modifier_threshold
        config = pack.checkpoint['config']
        context = config['max_length']
    else:
        schema = pack.checkpoint['schema']
        threshold = pack.checkpoint['trainingConfig']['modifier_threshold']
        context = pack.checkpoint['modelConfig']['context_bytes']
    manifest = json.loads((ROOT / 'packs' / pack_id / 'manifest.json').read_text())
    policy = {}
    config_path = source.parents[1] / 'pack.json'
    if config_path.exists():
        policy = json.loads(config_path.read_text()).get('decoder', {})
    if pack_id in {'html', 'vue'}:
        policy = {'coalesceAdjacentTokenTypes': [r for r in schema['tokenTypes'] if r.startswith('embedded-')],
                  'modifierRoles': {m: ['tag'] for m in schema['modifiers']}}
    sample = torch.randint(0, 256, (1, 64), dtype=torch.int64)
    path = output / 'model.onnx'
    torch.onnx.export(model, (sample,), str(path), input_names=['input_ids'],
                      output_names=['boundary', 'token_type', 'modifier'],
                      dynamic_shapes={'input_ids': {1: torch.export.Dim('bytes', min=1, max=context)}},
                      opset_version=18, dynamo=True, external_data=False)
    onnx.checker.check_model(onnx.load(path))
    session = ort.InferenceSession(str(path), providers=['CPUExecutionProvider'])
    comparisons = []
    for length in [1, 2, 7, 31, 64, 127, context - 1, context]:
        ids = torch.randint(0, 256, (1, length), dtype=torch.int64)
        with torch.inference_mode():
            native = pack.model(ids, torch.ones_like(ids, dtype=torch.bool))
        if pack_id == 'typescript':
            expected = (native.boundary_logits, native.token_type_logits, native.modifier_logits)
        else:
            expected = (native.boundary, native.token_type, native.modifier)
        actual = session.run(None, {'input_ids': ids.numpy()})
        errors = [float(np.max(np.abs(a.numpy() - b))) for a, b in zip(expected, actual)]
        if max(errors) >= 1e-4:
            raise ValueError(f'Export parity failed at {length} bytes: {errors}')
        comparisons.append({'bytes': length, 'maxAbsoluteErrors': errors})
    if digest(source) != source_hash:
        raise ValueError('Selected native model changed during export')
    record = {'format': 'nsh-browser-model-v1', 'id': pack_id, 'manifest': manifest,
              'model': {'file': 'model.onnx', 'sha256': digest(path), 'bytes': path.stat().st_size},
              'source': {'file': f'packs/{pack_id}/model/model.pt', 'sha256': source_hash},
              'contextBytes': context, 'schema': schema, 'modifierThreshold': threshold,
              'decoder': policy, 'quantized': False, 'resumableTrainingCheckpoint': False,
              'input': 'original-utf8-bytes', 'output': 'original-utf16-spans',
              'exporterSha256': digest(Path(__file__)), 'graphSha256': digest(Path(__file__).with_name('model.py'))}
    if pack.checkpoint.get('structuredDecoder') is not None:
        record['structuredDecoder'] = pack.checkpoint['structuredDecoder']
    (output / 'model.json').write_text(json.dumps(record, indent=2) + '\n')
    (output / 'verification.json').write_text(json.dumps({'reference': 'selected PyTorch CPU inference',
        'torch': str(torch.__version__), 'onnx': onnx.__version__, 'onnxruntime': ort.__version__,
        'sourceSha256': source_hash, 'modelSha256': digest(path), 'comparisons': comparisons}, indent=2) + '\n')
    print(json.dumps({'pack': pack_id, 'bytes': path.stat().st_size, 'sourcePreserved': True}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    export(args.pack, args.output or ROOT / 'packs' / args.pack / 'browser')
