"""Bounded original-curriculum refinement with immutable natural replay."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import time

import torch
from torch.utils.data import DataLoader, Subset

from dataset import TypeScriptSemanticDataset, build_adaptive_windows, encode_document, load_schema
from predict import load_model
from inference import predict_document_logits
from train import build_boundary_class_weights, build_token_type_class_weights, build_modifier_positive_weights, _optimizer_step
from training.shared.checkpoints import atomic_json, capture_rng, restore_rng, save_checkpoint, seed_all
from training.shared.inference import decode
from training.shared.metrics import SpanMetrics
from training.shared.model import ModelOutput
from training.shared.spec import file_hash


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--init-from',type=Path)
    parser.add_argument('--resume',type=Path)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--epochs',type=int,default=8)
    parser.add_argument('--local-kernel',type=int,choices=[1,3,5],default=1)
    parser.add_argument('--focus',type=Path)
    parser.add_argument('--eof-loss-weight',type=float,default=1.)
    args=parser.parse_args()
    if not 1<=args.eof_loss_weight<=32:raise ValueError('Source-end weight must be between one and 32')
    if bool(args.init_from)==bool(args.resume)or args.epochs<1:raise ValueError('Use one full checkpoint and a positive budget')
    source=args.resume or args.init_from
    if args.resume and (args.resume.name!='last.pt'or args.resume.parent.resolve()!=args.run.resolve()):raise ValueError('Resume last.pt in its existing run')
    if not args.resume and (args.run/'last.pt').exists():raise ValueError('Preserve existing run')
    device=torch.device('mps'if torch.backends.mps.is_available()else'cpu')
    if device.type=='cpu':torch.set_num_threads(4)
    seed_all(7251)
    root=Path.home()/'Datasets/neural-semantic-highlighting/typescript'
    focus_path=args.focus or root/'quality-regexp-20261119-10/focus.json'
    identity={str(p):file_hash(p)for p in [root/'train.json',root/'validation.json',focus_path]}
    raw=torch.load(source,map_location='cpu',weights_only=True)
    if not {'optimizer_state_dict','training_state','model_state_dict'}<=raw.keys():raise ValueError('A full training checkpoint is required')
    if args.resume and raw.get('qualityDataset')!=identity:raise ValueError('Resume dataset changed')
    quality_config=dict(eof_loss_weight=args.eof_loss_weight)
    if args.resume and raw.get('qualityConfig',dict(eof_loss_weight=1.))!=quality_config:raise ValueError('Resume preserves source-end loss policy')
    model,checkpoint=load_model(source,device)
    source_kernel=checkpoint['config'].get('local_kernel',1)
    if args.resume and args.local_kernel!=source_kernel:raise ValueError('Resume preserves local kernel')
    if not args.resume and source_kernel!=args.local_kernel:
        if source_kernel!=1 or args.local_kernel==1:raise ValueError('Incompatible local context transfer')
        width=checkpoint['config']['embedding_dimension']
        model.local_context=torch.nn.Conv1d(width,width,args.local_kernel,padding=args.local_kernel//2,groups=width).to(device)
        torch.nn.init.zeros_(model.local_context.weight);torch.nn.init.zeros_(model.local_context.bias)
        checkpoint['config']=dict(checkpoint['config'],local_kernel=args.local_kernel)
    schema=load_schema();ordered={'tokenTypes':list(schema.token_types),'modifiers':list(schema.modifiers)}
    all_natural=json.loads((root/'train.json').read_text())
    natural_validation=json.loads((root/'validation.json').read_text())
    rank=lambda d:hashlib.sha256((d['repository']+':'+d['path']).encode()).hexdigest()
    positives=[d for d in all_natural if any(s['tokenType']=='regexp'for s in d['result']['spans'])]
    negatives=[d for d in all_natural if not any(s['tokenType']=='regexp'for s in d['result']['spans'])]
    replay=sorted(positives,key=rank)[:100]+sorted(negatives,key=rank)[:200]
    assert not {(d['repository'],d['path'])for d in replay}&{(d['repository'],d['path'])for d in natural_validation}
    focus=json.loads(focus_path.read_text());focus_train=[d for d in focus if d['split']=='train'];focus_validation=[d for d in focus if d['split']=='validation']
    assert not {d['sourceGroup']for d in focus_train}&{d['sourceGroup']for d in focus_validation}
    dataset=object.__new__(TypeScriptSemanticDataset);dataset.schema=schema;dataset.max_length=512
    dataset.eof_loss_weight=args.eof_loss_weight
    dataset.documents=[encode_document(d,schema)for d in replay+focus_train]
    dataset.windows=[w for i,d in enumerate(dataset.documents)for w in build_adaptive_windows(i,d,max_length=512)[0]]
    replay_windows=[i for i,w in enumerate(dataset.windows)if w.document_index<len(replay)]
    focus_windows=[i for i,w in enumerate(dataset.windows)if w.document_index>=len(replay)]
    optimizer=torch.optim.AdamW(model.parameters(),lr=.00003,weight_decay=.01)
    boundary=torch.nn.CrossEntropyLoss(weight=build_boundary_class_weights(dataset).to(device),ignore_index=-100)
    token=torch.nn.CrossEntropyLoss(weight=build_token_type_class_weights(dataset).to(device),ignore_index=-100)
    modifiers=build_modifier_positive_weights(dataset).to(device)
    state=copy.deepcopy(raw['qualityState'])if args.resume else dict(bestScore=-1.,bestEpoch=0)
    first=raw.get('qualityEpoch',0)+1 if args.resume else 1
    base_epoch=raw['epoch']-raw.get('qualityEpoch',0) if args.resume else raw['epoch']
    provenance=copy.deepcopy(raw.get('qualityProvenance'))if args.resume else dict(
        initialCheckpoint=str(args.init_from),initialCheckpointHash=file_hash(source),
        mode='Explicit weights-only transfer; fresh optimizer; replay and original focus; no test use',
        codeHash=file_hash(Path(__file__)),focusManifestHash=file_hash(focus_path.parent/'manifest.json'))
    if args.resume:optimizer.load_state_dict(raw['optimizer_state_dict']);restore_rng(raw['qualityRng'],device)
    args.run.mkdir(parents=True,exist_ok=True)
    def evaluate():
        model.eval();metrics={key:SpanMetrics(ordered)for key in ['natural','focus']}
        for key,docs in [('natural',natural_validation),('focus',focus_validation)]:
            for d in docs:
                with torch.inference_mode():values=predict_document_logits(model,d['source'],max_length=512,device=device)
                metrics[key].add(d['result'],decode(d['source'],ModelOutput(*values),ordered,threshold=.5))
        return {k:v.report()for k,v in metrics.items()}
    baseline=evaluate()
    baseline_path=args.run/'baseline-validation.json'
    if not baseline_path.exists():atomic_json(baseline_path,baseline)
    original=json.loads(baseline_path.read_text())['natural']
    def selection(report):
        n=report['natural'];f=report['focus']['byTokenType']['regexp']['f1']
        if n['exactSpan']['f1']<original['exactSpan']['f1']-.003 or n['exactSpanMacroF1']<original['exactSpanMacroF1']-.015:return -1.
        return min(n['exactSpan']['f1'],f)
    if not args.resume:state['bestScore']=selection(baseline)
    if not args.resume:
        # The unchanged starting weights are a valid validation-selected candidate.
        # Save a complete fresh optimizer/RNG snapshot even if every update regresses.
        initial=copy.deepcopy(checkpoint)
        initial.update(epoch=base_epoch,model_state_dict=model.state_dict(),optimizer_state_dict=optimizer.state_dict(),
            qualityDataset=identity,qualityEpoch=0,qualityRng=capture_rng(device),qualityState=state.copy(),
            qualityConfig=quality_config,qualityProvenance=provenance,qualityValidation=baseline)
        initial.pop('structuredDecoder',None)
        save_checkpoint(args.run/'best.pt',initial)
    print('Device',device,'replay documents',len(replay),'focus',len(focus_train),'windows',len(dataset.windows),'baseline score',state['bestScore'],flush=True)
    for epoch in range(first,first+args.epochs):
        start=time.monotonic();model.train()
        rng=random.Random(7251+epoch);indices=rng.sample(replay_windows,min(len(replay_windows),len(focus_windows)))+focus_windows
        rng.shuffle(indices);loader=DataLoader(Subset(dataset,indices),batch_size=32,shuffle=False,num_workers=0)
        losses=[]
        for batch in loader:
            losses.append(_optimizer_step(model,batch,optimizer,boundary,token,modifiers,device,.1,include_modifier=True)[0])
        report=evaluate();score=selection(report);improved=score>state['bestScore']
        if improved:state.update(bestScore=score,bestEpoch=epoch)
        if not all(bool(torch.isfinite(p).all())for p in model.parameters()):raise ValueError('Nonfinite parameters; no checkpoint advanced')
        payload=copy.deepcopy(checkpoint);payload.update(epoch=base_epoch+epoch,model_state_dict=model.state_dict(),optimizer_state_dict=optimizer.state_dict(),
            qualityDataset=identity,qualityEpoch=epoch,qualityRng=capture_rng(device),qualityState=state.copy(),
            qualityConfig=quality_config,
            qualityProvenance=provenance,
            qualityValidation=report)
        payload.pop('structuredDecoder',None)
        save_checkpoint(args.run/'last.pt',payload)
        if improved:save_checkpoint(args.run/'best.pt',payload)
        atomic_json(args.run/f'epoch-{epoch:04d}.json',dict(epoch=epoch,seconds=time.monotonic()-start,loss=sum(losses)/len(losses),selection=score,metrics=report))
        print('epoch',epoch,'seconds',round(time.monotonic()-start,1),'natural',round(report['natural']['exactSpan']['f1'],5),
              'focus regexp',round(report['focus']['byTokenType']['regexp']['f1'],5),'selection',score,flush=True)
    print('Done',args.run,flush=True)


if __name__=='__main__':main()
