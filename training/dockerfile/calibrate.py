"""Freeze train-fitted joint decoding, selected on natural validation only."""
from pathlib import Path
import argparse
import copy
import json

from training.shared.checkpoints import atomic_json, load_checkpoint, save_checkpoint
from training.shared.inference import decode, document_logits
from training.shared.metrics import SpanMetrics
from training.shared.prepare import file_hash
from training.shared.runtime import LocalPack
from training.shared.spec import using
from training.shared.structured import fit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', default='auto', choices=['auto', 'cpu', 'mps', 'cuda'])
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Preserve existing calibrated checkpoints')
    source_hash = file_hash(args.checkpoint)
    checkpoint = load_checkpoint(args.checkpoint)
    pack = LocalPack(checkpoint_path=args.checkpoint, device_name=args.device)
    snapshot = Path(checkpoint['dataset']['path']).expanduser()
    def natural(split):
        return [d for line in (snapshot / split / 'documents.jsonl').read_text().splitlines()
                if (d := json.loads(line))['stream'] == 'natural']
    train, validation = natural('train'), natural('validation')
    if {d['sourceGroup'] for d in train} & {d['sourceGroup'] for d in validation}:
        raise ValueError('Training/validation families overlap')
    cached = [(d, document_logits(pack.model, d['source'], pack.device)) for d in validation]
    # One predetermined grid; no test source or predictions enter this command.
    parameters = fit(train, checkpoint['schema'], type_weight=.25, transition_weight=.3)
    trials = []
    for alpha in (.1, .25, .5, 1.):
        for weight in (.1, .3, .5):
            candidate = {**parameters, 'typeWeight': alpha, 'transitionWeight': weight}
            metrics = {'natural': SpanMetrics(checkpoint['schema'])}
            for doc, logits in cached:
                predicted = decode(doc['source'], logits, checkpoint['schema'],
                    threshold=checkpoint['trainingConfig']['modifier_threshold'],
                    structured_decoder=candidate, **pack.spec.decoder())
                metrics['natural'].add(doc['result'], predicted)
            reports = {name: value.report() for name, value in metrics.items()}
            score = reports['natural']['exactSpanMacroF1']
            trials.append(dict(typeWeight=alpha, transitionWeight=weight, selectionScore=score, metrics=reports))
            print(alpha, weight, {k: round(v['exactSpan']['f1'], 5) for k, v in reports.items()}, flush=True)
    selected = max(trials, key=lambda row: (row['selectionScore'], row['metrics']['natural']['exactSpan']['f1']))
    checkpoint = copy.deepcopy(checkpoint)
    checkpoint['structuredDecoder'] = {**parameters, 'typeWeight': selected['typeWeight'],
                                       'transitionWeight': selected['transitionWeight']}
    report = dict(sourceCheckpoint=str(args.checkpoint), sourceCheckpointHash=source_hash,
        dataset=checkpoint['dataset'], frozenGroupsHash=file_hash(Path('packs/dockerfile/dataset/split-groups.json')),
        fit='Laplace-smoothed legal BIO/role transitions on natural TRAIN Gold only',
        selection='Natural real-source adaptive validation role macro F1; exact-span micro F1 breaks ties',
        primaryTestUsed=False, trials=trials, selected=selected)
    report_path = args.output.with_suffix('.calibration.json')
    if report_path.exists() or file_hash(args.checkpoint) != source_hash:
        raise ValueError('Preserve calibration evidence and frozen source checkpoint')
    atomic_json(report_path, report)
    checkpoint['decoderCalibration'] = dict(sourceCheckpointHash=source_hash,
        validationReport=str(report_path), validationReportHash=file_hash(report_path),
        frozenGroupsHash=report['frozenGroupsHash'], selection=report['selection'], primaryTestUsed=False)
    save_checkpoint(args.output, checkpoint)
    print('Frozen:', args.output, flush=True)


if __name__ == '__main__':
    with using('dockerfile'):
        main()
