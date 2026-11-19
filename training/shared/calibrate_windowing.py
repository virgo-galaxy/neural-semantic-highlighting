"""Select bounded neural overlap/fusion using natural validation only."""
from pathlib import Path
import argparse
import copy
import json
import torch
from training.shared.checkpoints import atomic_json, load_checkpoint, save_checkpoint
from training.shared.inference import decode, cursor_logits
from training.shared.model import ModelOutput
from training.shared.windowing import overlap_logits
from training.shared.metrics import SpanMetrics
from training.shared.runtime import LocalPack
from training.shared.spec import using, file_hash
from training.shared.trainer_data import Snapshot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    if args.output.exists() or args.output.with_suffix('.windowing.json').exists():
        raise ValueError('Preserve previous windowing evidence')
    torch.set_num_threads(4)
    with using(args.pack) as spec:
        source_hash=file_hash(args.checkpoint)
        checkpoint=load_checkpoint(args.checkpoint)
        snapshot=Snapshot.open(Path(checkpoint['dataset']['path']))
        if snapshot.identity()!={k:checkpoint['dataset'][k]for k in ['snapshot','manifestHash']}:
            raise ValueError('Validation snapshot identity mismatch')
        snapshot.verify_split('validation')
        documents=[d for d in map(json.loads,(snapshot.path/'validation/documents.jsonl').read_text().splitlines())if d['stream']=='natural']
        if {d['profile']for d in documents}!=set(spec.profiles):
            raise ValueError('Every profile requires natural validation evidence')
        training_groups={d['sourceGroup']for d in map(json.loads,(snapshot.path/'train/documents.jsonl').read_text().splitlines())}
        if training_groups & {d['sourceGroup']for d in documents}:
            raise ValueError('Training and validation families overlap')
        pack=LocalPack(checkpoint_path=args.checkpoint,device_name='cpu')
        candidates=[checkpoint.get('inferenceWindowing')]+[dict(format='nsh-overlap-logits-v1',strideBytes=stride,edgeWeightCap=128,adaptiveWeight=weight)for stride in [256,128]for weight in [0,.5]]
        cached=[]
        for d in documents:
            original=cursor_logits(pack.model,d['source'],pack.device)
            overlap={};windows={}
            if len(d['source'].encode('utf-8'))>512:
                for stride in [256,128]:
                    policy=dict(format='nsh-overlap-logits-v1',strideBytes=stride,edgeWeightCap=128,adaptiveWeight=0)
                    overlap[stride]=overlap_logits(pack.model,d['source'],pack.device,policy,window_cache=windows)
            cached.append((d,original,overlap))
        trials=[];best=None;baseline_macro=None
        for policy in candidates:
            pack.model.inference_windowing=policy
            metrics={p:SpanMetrics(checkpoint['schema'])for p in spec.profiles};aggregate=SpanMetrics(checkpoint['schema'])
            for d,original,overlap in cached:
                logits=original
                if policy is not None and overlap:
                    other=overlap[policy['strideBytes']];weight=policy['adaptiveWeight']
                    logits=other if not weight else ModelOutput(*[a.double()*weight+b*(1-weight)for a,b in zip(
                        [original.boundary,original.token_type,original.modifier],[other.boundary,other.token_type,other.modifier])])
                result=decode(d['source'],logits,checkpoint['schema'],
                    threshold=checkpoint['trainingConfig']['modifier_threshold'],structured_decoder=checkpoint.get('structuredDecoder'),**spec.decoder())
                metrics[d['profile']].add(d['result'],result);aggregate.add(d['result'],result)
            reports={p:m.report()for p,m in metrics.items()};macro=sum(m['exactSpanMacroF1']for m in reports.values())/len(reports)
            key=(min(m['exactSpan']['f1']for m in reports.values()),macro)
            if baseline_macro is None:baseline_macro=macro
            row=dict(index=len(trials),policy=policy,selectionKey=list(key),profiles=reports,natural=aggregate.report());trials.append(row)
            if macro>=baseline_macro-.01 and(best is None or key>tuple(best['selectionKey'])):best=row
            print(args.pack,policy,[round(v,5)for v in key],flush=True)
        report=dict(format='nsh-windowing-validation-v1',sourceCheckpointHash=source_hash,dataset=checkpoint['dataset'],
            calibrationCodeSha256=file_hash(Path(__file__)),windowingCodeSha256=file_hash(Path(__file__).with_name('windowing.py')),
            selection='Maximum minimum natural VALIDATION profile F1; role macro decrease at most .01; unchanged runtime eligible',
            testPredictionsUsed=False,trials=trials,selected=best['index'])
        report_path=args.output.with_suffix('.windowing.json');atomic_json(report_path,report)
        frozen=copy.deepcopy(checkpoint)
        if best['policy']is None:frozen.pop('inferenceWindowing',None)
        else:frozen['inferenceWindowing']=best['policy']
        frozen['windowingCalibration']=dict(validationReport=str(report_path),validationReportHash=file_hash(report_path),testPredictionsUsed=False)
        if file_hash(args.checkpoint)!=source_hash:raise ValueError('Frozen source changed')
        save_checkpoint(args.output,frozen)


if __name__=='__main__':main()
