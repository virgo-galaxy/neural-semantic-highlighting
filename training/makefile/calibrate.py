"""Freeze train-fitted joint BIO decoding using fresh/legacy natural validation."""
from pathlib import Path
import argparse
import copy
import json
from training.shared.checkpoints import atomic_json,load_checkpoint,save_checkpoint
from training.shared.inference import decode,document_logits
from training.shared.metrics import SpanMetrics
from training.shared.prepare import file_hash
from training.shared.runtime import LocalPack
from training.shared.spec import using
from training.shared.structured import fit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--device',default='cpu',choices=['auto','cpu','mps','cuda'])
    parser.add_argument('--baseline-validation',type=Path,help='Optional frozen baseline validation comparison; maximize balanced F1 gains')
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Preserve existing calibrated checkpoints')
    source_hash=file_hash(args.checkpoint);checkpoint=load_checkpoint(args.checkpoint)
    pack=LocalPack(checkpoint_path=args.checkpoint,device_name=args.device)
    snapshot=Path(checkpoint['dataset']['path']).expanduser()
    def natural(split):return [d for line in(snapshot/split/'documents.jsonl').read_text().splitlines()if(d:=json.loads(line))['stream']=='natural']
    train,validation=natural('train'),natural('validation')
    protocol=Path('packs/makefile/dataset/optimization-protocol.json');allocation=json.loads(protocol.read_text());fresh=set(allocation['freshValidationSourceGroups'])
    if {d['sourceGroup']for d in train}&{d['sourceGroup']for d in validation}:raise ValueError('Training and validation overlap')
    if not any(d['sourceGroup']in fresh for d in validation)or not any(d['sourceGroup']not in fresh for d in validation):raise ValueError('Both fresh and legacy validation are required')
    cached=[(d,document_logits(pack.model,d['source'],pack.device))for d in validation]
    baseline=json.loads(args.baseline_validation.read_text()) if args.baseline_validation else None
    if baseline is not None:
        expected={(d['sourceGroup'],d['contentHash'])for d in validation}
        if baseline.get('split')!='validation' or {(d['sourceGroup'],d['contentHash'])for d in baseline['cases']}!=expected:
            raise ValueError('Baseline must contain exactly the same natural validation sources')
    parameters=fit(train,checkpoint['schema'],type_weight=.25,transition_weight=.3);trials=[]
    for alpha in (.1,.25,.5,1.):
        for weight in (.1,.3,.5,1.,2.):
            candidate={**parameters,'typeWeight':alpha,'transitionWeight':weight}
            metrics={name:SpanMetrics(checkpoint['schema'])for name in ['all','fresh','legacy']}
            for doc,logits in cached:
                predicted=decode(doc['source'],logits,checkpoint['schema'],threshold=checkpoint['trainingConfig']['modifier_threshold'],structured_decoder=candidate,**pack.spec.decoder())
                metrics['all'].add(doc['result'],predicted);metrics['fresh'if doc['sourceGroup']in fresh else'legacy'].add(doc['result'],predicted)
            reports={name:m.report()for name,m in metrics.items()};score=min(m['exactSpan']['f1']-(baseline['cohorts'][name]['exactSpan']['f1']if baseline else 0.)for name,m in reports.items())
            trials.append(dict(typeWeight=alpha,transitionWeight=weight,selectionScore=score,metrics=reports))
            print(alpha,weight,{k:round(m['exactSpan']['f1'],5)for k,m in reports.items()},flush=True)
    selected=max(trials,key=lambda row:(row['selectionScore'],row['metrics']['all']['exactSpanMacroF1']))
    checkpoint=copy.deepcopy(checkpoint);checkpoint['structuredDecoder']={**parameters,'typeWeight':selected['typeWeight'],'transitionWeight':selected['transitionWeight']}
    report=dict(sourceCheckpoint=str(args.checkpoint),sourceCheckpointHash=source_hash,dataset=checkpoint['dataset'],protocolHash=file_hash(protocol),fit='Laplace-smoothed legal BIO/role transitions on natural TRAIN Gold only',selection=('Maximum minimum original exact-span F1 GAIN over the frozen baseline on all/fresh/legacy natural VALIDATION; role macro breaks ties'if baseline else'Maximum minimum exact-span F1 of all/fresh/legacy natural VALIDATION; role macro breaks ties'),primaryTestUsed=False,calibratorSha256=file_hash(Path(__file__)),trials=trials,selected=selected)
    if baseline is not None:
        report['baselineValidation']=dict(path=str(args.baseline_validation),sha256=file_hash(args.baseline_validation),checkpointHash=baseline['checkpointHash'],cohorts=baseline['cohorts'])
    report_path=args.output.with_suffix('.calibration.json')
    if report_path.exists()or file_hash(args.checkpoint)!=source_hash:raise ValueError('Preserve calibration evidence and frozen source')
    atomic_json(report_path,report)
    checkpoint['decoderCalibration']=dict(sourceCheckpointHash=source_hash,validationReport=str(report_path),validationReportHash=file_hash(report_path),protocolHash=file_hash(protocol),selection=report['selection'],calibratorSha256=report['calibratorSha256'],primaryTestUsed=False)
    save_checkpoint(args.output,checkpoint);print('Frozen:',args.output,flush=True)


if __name__=='__main__':
    with using('makefile'):main()
