"""Parser-free runtime shared by standalone neural language packs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import torch
from training.shared.spec import current, using
from training.shared.checkpoints import load_model_artifact, model_from_checkpoint, select_device
from training.shared.inference import decode, document_logits

class LocalPack:
    def __init__(self, *, pack_id=None, checkpoint_path=None, device_name='auto'):
        pack_id = pack_id or current().id
        with using(pack_id) as spec:
            self.spec = spec
            self.device = select_device(device_name)
            if self.device.type == 'cpu': torch.set_num_threads(min(4,torch.get_num_threads()))
            path=Path(checkpoint_path or spec.directory/'model/model.pt')
            self.checkpoint=load_model_artifact(path)
            spec.verify_config(self.checkpoint.get('provenance',{}))
            if self.checkpoint['schema'] != spec.schema() or self.checkpoint.get('documentKinds') != list(spec.document_kinds):
                raise ValueError('Artifact does not match pack schema/document kinds')
            self.model=model_from_checkpoint(self.checkpoint,self.device)
            self.model.eval()

    def highlight(self, *, source, document_kind):
        if not isinstance(source,str) or document_kind not in self.spec.document_kinds:
            raise ValueError('Unsupported source or document kind')
        return decode(source,document_logits(self.model,source,self.device),self.checkpoint['schema'],
                      threshold=self.checkpoint['trainingConfig']['modifier_threshold'],
                      structured_decoder=getattr(self.model, 'structured_decoder', None), **self.spec.decoder())

def run_stdio(pack):
    for line in sys.stdin:
        if not line.strip():continue
        request_id=None
        try:
            request=json.loads(line)
            if not isinstance(request,dict):raise ValueError('Request must be an object')
            request_id=request.get('id')
            result=pack.highlight(source=request['source'],document_kind=request['documentKind'])
            response={'id':request_id,'result':result}
        except Exception as error:response={'id':request_id,'error':{'message':str(error)}}
        print(json.dumps(response,ensure_ascii=False,separators=(',',':')),flush=True)

def main():
    spec=current()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,default=spec.directory/'model/model.pt')
    parser.add_argument('--device',default='auto',choices=['auto','cpu','mps','cuda'])
    parser.add_argument('--document-kind',default=spec.document_kinds[0],choices=spec.document_kinds)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--stdio',action='store_true');modes.add_argument('--text');modes.add_argument('--file',type=Path)
    args=parser.parse_args()
    pack=LocalPack(checkpoint_path=args.checkpoint,device_name=args.device)
    if args.stdio:run_stdio(pack)
    else:
        source=args.file.read_bytes().decode('utf-8') if args.file else args.text
        print(json.dumps(pack.highlight(source=source,document_kind=args.document_kind),ensure_ascii=False,indent=2))
