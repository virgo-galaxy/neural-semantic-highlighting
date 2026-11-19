"""Validation-only convex averaging of compatible full pack checkpoints."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess

import torch

from training.shared.checkpoints import atomic_json, capture_rng, load_checkpoint, model_from_checkpoint, save_checkpoint
from training.shared.inference import decode, document_logits
from training.shared.metrics import SpanMetrics, evaluate_fixed
from training.shared.model import ModelConfig
from training.shared.provenance import code_hashes
from training.shared.spec import current, file_hash, using
from training.shared.train import selection_score
from training.shared.trainer_data import Snapshot, WindowSplit


def blend(states, weights):
    if (not states or len(states)!=len(weights)or any(type(w)not in(int,float)or not 0<=w<=1 for w in weights)
            or abs(sum(weights)-1)>1e-8):raise ValueError('Expected convex averaging weights')
    template=states[0]
    if any(set(s)!=set(template)or any(s[k].shape!=v.shape or s[k].dtype!=v.dtype for k,v in template.items())for s in states):
        raise ValueError('Averaging requires compatible ordered model tensors')
    return {k:sum(s[k].double()*w for s,w in zip(states,weights)).to(v.dtype)for k,v in template.items()}


def assert_holdouts(train_groups,heldout_groups):
    if set(train_groups)&set(heldout_groups):raise ValueError('A parent checkpoint trained on a target held-out family')


def run(paths, output):
    if output.exists()or output.with_suffix('.averaging.json').exists():raise ValueError('Preserve previous weight-averaging experiments')
    checkpoints=[load_checkpoint(path)for path in paths]
    target=checkpoints[0];snapshot=Snapshot.open(Path(target['dataset']['path']))
    if snapshot.identity()!={k:target['dataset'][k]for k in ['snapshot','manifestHash']}:raise ValueError('Target dataset identity mismatch')
    def documents(folder,split):return [json.loads(line)for line in(folder/split/'documents.jsonl').read_text().splitlines()]
    # Read only family identities from target holdouts; never their predictions.
    heldout={d['sourceGroup']for split in ['validation','test']for d in documents(snapshot.path,split)}
    validation=[d for d in documents(snapshot.path,'validation')if d['stream']=='natural']
    config=copy.deepcopy(target['modelConfig']);config['local_kernel']=5
    target_model=copy.deepcopy(target);target_model['modelConfig']=config
    states=[]
    from training.shared.model import SemanticTransformer
    template=SemanticTransformer(ModelConfig(**config),len(target['schema']['tokenTypes']),len(target['schema']['modifiers'])).state_dict()
    for checkpoint in checkpoints:
        current().verify_config(checkpoint.get('provenance',{}))
        a=ModelConfig(**checkpoint['modelConfig']).to_dict();b=ModelConfig(**config).to_dict()
        a.pop('local_kernel');b.pop('local_kernel')
        a.pop('relative_attention');b.pop('relative_attention')
        if (checkpoint['trainingConfig'].get('smoke')or checkpoint['schema']!=target['schema']or a!=b):raise ValueError('Incompatible parent experiment')
        assert_holdouts({d['sourceGroup']for d in documents(Path(checkpoint['dataset']['path']),'train')},heldout)
        original=checkpoint['model'];state={}
        if 'relative_bias'in original and 'relative_bias'not in template:raise ValueError('Cannot discard learned relative attention')
        for key,value in template.items():
            if key in original:state[key]=original[key]
            elif key.startswith('local_context.')and checkpoint['modelConfig'].get('local_kernel',1)==1:state[key]=torch.zeros_like(value)
            elif key=='relative_bias'and not checkpoint['modelConfig'].get('relative_attention',False):state[key]=torch.zeros_like(value)
            else:raise ValueError('Incompatible tensor '+key)
        states.append(state)
    target_model['model']=states[0]
    model=model_from_checkpoint(target_model,torch.device('cpu')).eval()
    primary_decoder=target.get('structuredDecoder')
    def measure(decoder,cached):
        metrics={p:SpanMetrics(target['schema'])for p in current().profiles}
        aggregate=SpanMetrics(target['schema'])
        for d,logits in cached:
            result=decode(d['source'],logits,target['schema'],threshold=target['trainingConfig']['modifier_threshold'],
                structured_decoder=decoder,**current().decoder())
            metrics[d['profile']].add(d['result'],result);aggregate.add(d['result'],result)
        reports={p:m.report()for p,m in metrics.items()}
        key=(min(m['exactSpan']['f1']for m in reports.values()),sum(m['exactSpanMacroF1']for m in reports.values())/len(reports))
        return key,dict(profiles=reports,natural=aggregate.report())
    n=len(states);vectors=[[1.]+[0.]*(n-1)]
    if n>1:
        vectors += [[.75]+[.25/(n-1)]*(n-1),[.5]+[.5/(n-1)]*(n-1),[1/n]*n]
    trials=[];best=None;baseline_macro=None
    for index,weights in enumerate(vectors):
        state=blend(states,weights);model.load_state_dict(state)
        cached=[(d,document_logits(model,d['source'],torch.device('cpu')))for d in validation]
        for use_decoder in ([True,False]if primary_decoder else[False]):
            key,report=measure(primary_decoder if use_decoder else None,cached)
            if baseline_macro is None:baseline_macro=key[1]
            row=dict(weights=weights,primaryDecoder=use_decoder,selectionKey=list(key),metrics=report)
            trials.append(row)
            if key[1]>=baseline_macro-.03 and(best is None or key>best[0]):best=(key,state,row)
            print(index,use_decoder,[round(v,5)for v in key],flush=True)
    key,state,row=best
    evidence=dict(pack=current().id,selection='Maximum minimum natural VALIDATION profile F1; mean role macro tie-break; at most .03 macro decrease',
        parents=[dict(path=str(p),sha256=file_hash(p),dataset=c['dataset'],epoch=c['epoch'])for p,c in zip(paths,checkpoints)],
        testPredictionsUsed=False,trials=trials,selected=row)
    report_path=output.with_suffix('.averaging.json');atomic_json(report_path,evidence)
    frozen=copy.deepcopy(target);frozen['modelConfig']=config;frozen['model']=state
    frozen['trainingConfig']=dict(target['trainingConfig'],selection_metric='minimum-profile-f1'if len(current().profiles)>1 else'profile-f1')
    if frozen['trainingConfig'].get('ascii_case_tied')and not torch.equal(state['byte_embedding.weight'][65:91],state['byte_embedding.weight'][97:123]):
        frozen['trainingConfig']['ascii_case_tied']=False
    frozen.pop('structuredDecoder',None);frozen.pop('decoderCalibration',None)
    model.load_state_dict(state);model.structured_decoder=None
    split=WindowSplit(snapshot,'validation')
    try:fixed=evaluate_fixed(model,split,torch.device('cpu'),threshold=target['trainingConfig']['modifier_threshold'],log_every=100)
    finally:split.close()
    frozen['validation']=fixed
    optimizer=torch.optim.AdamW(model.parameters(),lr=target['trainingConfig']['learning_rate'],weight_decay=target['trainingConfig']['weight_decay'])
    frozen['optimizer']=optimizer.state_dict();frozen['rng']=capture_rng(torch.device('cpu'))
    strategy=frozen['trainingConfig'].get('selection_metric','profile-macro')
    frozen['trainingState']=dict(bestScore=selection_score(fixed,strategy),bestEpoch=frozen['epoch'],epochsWithoutImprovement=0,optimizerSteps=0)
    frozen['weightAveraging']=dict(report=str(report_path),reportHash=file_hash(report_path),parents=evidence['parents'],weights=row['weights'],
        testPredictionsUsed=False,optimizer='Explicitly reset AdamW; complete resumable CPU RNG; post-training stage at primary source epoch')
    frozen['provenance']=dict(codeHashes=code_hashes(),semanticsHash=file_hash(current().semantics_path),packConfigHash=file_hash(current().directory/'pack.json'),
        decoderPolicy=current().decoder(),pythonTorch=str(torch.__version__),repositoryCommit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),repositoryDirty=True)
    save_checkpoint(output,frozen)
    print('Frozen',output,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack',required=True);parser.add_argument('--checkpoints',type=Path,nargs='+',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();torch.set_num_threads(4)
    with using(args.pack):run(args.checkpoints,args.output)


if __name__=='__main__':main()
