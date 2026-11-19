"""Select optional train-fitted BIO/role decoding using natural validation only."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from training.shared.checkpoints import atomic_json, load_checkpoint, save_checkpoint
from training.shared.inference import decode, document_logits
from training.shared.metrics import SpanMetrics
from training.shared.prepare import file_hash
from training.shared.runtime import LocalPack
from training.shared.spec import current, using
from training.shared.structured import fit
from training.shared.trainer_data import Snapshot


def validate_partitions(train, validation, profiles):
    if not train or not validation or any(d['stream'] != 'natural' for d in train + validation):
        raise ValueError('Calibration requires natural train and validation documents')
    if {d['sourceGroup'] for d in train} & {d['sourceGroup'] for d in validation}:
        raise ValueError('Training/validation families overlap')
    if {d['profile'] for d in validation} != set(profiles):
        raise ValueError('Every profile needs natural validation evidence')


def selection_key(reports):
    values = list(reports.values())
    return (sum(v['exactSpanMacroF1'] for v in values) / len(values),
            min(v['exactSpan']['f1'] for v in values))


def calibrate(checkpoint_path: Path, output: Path, device: str):
    report_path = output.with_suffix('.calibration.json')
    if output.exists() or report_path.exists():
        raise ValueError('Preserve existing checkpoint and calibration evidence')
    source_hash = file_hash(checkpoint_path)
    checkpoint = load_checkpoint(checkpoint_path)
    snapshot = Snapshot.open(Path(checkpoint['dataset']['path']))
    if snapshot.identity() != {k: checkpoint['dataset'][k] for k in ('snapshot', 'manifestHash')}:
        raise ValueError('Calibration snapshot differs from checkpoint')
    def natural(split):
        snapshot.verify_split(split)
        return [d for line in (snapshot.path / split / 'documents.jsonl').read_text().splitlines()
                if (d := json.loads(line))['stream'] == 'natural']
    train, validation = natural('train'), natural('validation')
    validate_partitions(train, validation, current().profiles)
    pack = LocalPack(checkpoint_path=checkpoint_path, device_name=device)
    cached = [(d, document_logits(pack.model, d['source'], pack.device)) for d in validation]
    parameters = fit(train, checkpoint['schema'], type_weight=.25, transition_weight=.3)
    # Include the unchanged decoder. Calibration may never force a worse choice.
    candidates = [checkpoint.get('structuredDecoder')]
    candidates += [{**parameters, 'typeWeight': alpha, 'transitionWeight': weight}
                   for alpha in (.1, .25, .5, 1.) for weight in (.1, .3, .5)]
    trials = []
    for index, candidate in enumerate(candidates):
        metrics = {p: SpanMetrics(checkpoint['schema']) for p in current().profiles}
        aggregate = SpanMetrics(checkpoint['schema'])
        for doc, logits in cached:
            predicted = decode(doc['source'], logits, checkpoint['schema'],
                               threshold=checkpoint['trainingConfig']['modifier_threshold'],
                               structured_decoder=candidate, **pack.spec.decoder())
            metrics[doc['profile']].add(doc['result'], predicted)
            aggregate.add(doc['result'], predicted)
        reports = {p: m.report() for p, m in metrics.items()}
        key = selection_key(reports)
        trials.append(dict(index=index, parameters=candidate, selectionKey=list(key),
                           profiles=reports, natural=aggregate.report()))
        print(index, 'selection', [round(v, 5) for v in key],
              'F1', round(aggregate.report()['exactSpan']['f1'], 5), flush=True)
    selected = max(trials, key=lambda row: tuple(row['selectionKey']))
    report = dict(pack=current().id, sourceCheckpoint=str(checkpoint_path),
                  sourceCheckpointHash=source_hash, dataset=checkpoint['dataset'],
                  fit='Natural TRAIN Gold only; source-family disjoint VALIDATION selection',
                  selection='Mean per-profile natural adaptive role macro F1; minimum profile micro F1 breaks ties',
                  testUsed=False, trials=trials, selected=selected['index'])
    if file_hash(checkpoint_path) != source_hash:
        raise ValueError('Source checkpoint changed during calibration')
    frozen = copy.deepcopy(checkpoint)
    if selected['parameters'] is None:
        frozen.pop('structuredDecoder', None)
    else:
        frozen['structuredDecoder'] = selected['parameters']
    atomic_json(report_path, report)
    frozen['decoderCalibration'] = dict(sourceCheckpointHash=source_hash,
        validationReport=str(report_path), validationReportHash=file_hash(report_path),
        selection=report['selection'], primaryTestUsed=False)
    save_checkpoint(output, frozen)
    print('Frozen:', output, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', choices=['auto', 'mps', 'cpu', 'cuda'], default='auto')
    args = parser.parse_args()
    with using(args.pack):
        calibrate(args.checkpoint, args.output, args.device)


if __name__ == '__main__':
    main()
