"""Export a reviewed full TypeScript refinement checkpoint without optimizer state."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import torch

from training.portable import portable_data

from training.shared.checkpoints import atomic_json, save_checkpoint
from training.shared.spec import file_hash

ROOT = Path(__file__).resolve().parents[2]


def export_model(source: Path, report_path: Path, output: Path) -> dict:
    if output.exists() or output.with_name('model.json').exists():
        raise ValueError('Preserve the previous inference bundle; stage a new output')
    source_hash = file_hash(source)
    checkpoint = torch.load(source, map_location='cpu', weights_only=True)
    required = {'model_state_dict', 'optimizer_state_dict', 'training_state', 'qualityValidation',
                'qualityProvenance', 'qualityDataset', 'qualityState', 'qualityRng'}
    if (checkpoint.get('format') != 'nsh-typescript-checkpoint' or not required <= checkpoint.keys()
            or checkpoint['config']['max_length'] != 512):
        raise ValueError('Expected a full, reviewed 512-byte TypeScript refinement checkpoint')
    report = json.loads(report_path.read_text())
    if report.get('checkpointHash') != source_hash:
        raise ValueError('Review must identify these exact frozen weights')
    for name in ['legacyNaturalTest', 'authoredFirstHoldout', 'realProductFirstHoldout']:
        result = report['corpora'][name]['candidate']
        if result['metrics']['documents'] < 1 or len(result['datasetHash']) != 64:
            raise ValueError('Missing natural, focused or actual-product review evidence')
    for name, digest in checkpoint['qualityDataset'].items():
        if file_hash(Path(name)) != digest:
            raise ValueError('Refinement data differs from its frozen identity')
    if file_hash(source) != source_hash:
        raise ValueError('Source changed while loading')
    for name in ['README.md', 'BENCHMARKS.md', 'KNOWN_ISSUES.md']:
        if not (output.parent / name).exists():
            raise ValueError('Prepare model documentation before export')
    artifact = {key: checkpoint[key] for key in ['format', 'model_state_dict', 'schema', 'config', 'epoch']}
    artifact['validation'] = checkpoint['qualityValidation']
    artifact = portable_data(artifact)
    save_checkpoint(output, artifact)
    reloaded = torch.load(output, map_location='cpu', weights_only=True)
    if any(not torch.equal(value, reloaded['model_state_dict'][key]) for key, value in artifact['model_state_dict'].items()):
        raise ValueError('Export changed model tensors')
    metadata = copy.deepcopy(json.loads((ROOT / 'packs/typescript/model/model.json').read_text()))
    metadata['artifact'] = dict(file=output.name, format=artifact['format'], sha256=file_hash(output),
        bytes=output.stat().st_size, parameterCount=sum(t.numel() for t in artifact['model_state_dict'].values()),
        tensorCount=len(artifact['model_state_dict']), dtypes=sorted({str(t.dtype).removeprefix('torch.') for t in artifact['model_state_dict'].values()}),
        containsOptimizerState=False, resumableTrainingCheckpoint=False)
    metadata['selection'] = dict(epoch=checkpoint['epoch'],
        metric='Minimum natural validation F1 and authored validation RegExp F1; natural micro/macro regression guards',
        score=checkpoint['qualityState']['bestScore'])
    metadata['checkpointConfig'] = checkpoint['config']
    metadata['validation'] = checkpoint['qualityValidation']
    metadata['provenance'] = dict(sourceCheckpoint=str(source.resolve()), sourceCheckpointSha256=source_hash,
        qualityProvenance=checkpoint['qualityProvenance'], qualityDataset=checkpoint['qualityDataset'],
        qualityConfig=checkpoint.get('qualityConfig', {}), exporterSha256=file_hash(Path(__file__)),
        trainingCodeSha256={str(p.relative_to(ROOT)): file_hash(p) for p in (ROOT / 'training/typescript').glob('*.py')})
    reports = output.parent / 'reports'
    reports.mkdir(exist_ok=True)
    target = reports / 'quality-test.json'
    public_report = copy.deepcopy(report)
    public_report['detailPolicy'] = 'Per-file diagnostics compacted; aggregate metrics unchanged; full report retained with the experiment'
    public_report['fullReportSha256'] = file_hash(report_path)
    for cohort in public_report['corpora'].values():
        for result in cohort.values():
            for row in result['files']:
                metrics = row.pop('metrics')
                row['f1'] = metrics['exactSpan']['f1']
                row['roleMacroF1'] = metrics['exactSpanMacroF1']
    atomic_json(target, portable_data(public_report))
    metadata['reports'] = {'quality-test.json': dict(file='reports/quality-test.json', sha256=file_hash(target),
        checkpointHash=source_hash, scope=report['scope'])}
    metadata.pop('exportVerification', None)
    atomic_json(output.with_name('model.json'), portable_data(metadata))
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--test-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_model(args.checkpoint, args.test_report, args.output)['artifact'], indent=2))


if __name__ == '__main__':
    main()
