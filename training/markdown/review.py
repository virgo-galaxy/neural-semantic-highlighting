"""Review visible Markdown probes and actual natural validation, never the test split."""
import argparse
import json
from pathlib import Path
from packs.markdown.labeling.label import label
from training.shared.metrics import SpanMetrics
from training.shared.runtime import LocalPack
from training.shared.spec import REPOSITORY, using, file_hash


def compare(pack, source, gold):
    predicted = pack.highlight(source=source, document_kind='markdown')
    metric = SpanMetrics(pack.checkpoint['schema']); metric.add(gold,predicted)
    def key(s): return s['start'],s['end'],s['tokenType'],tuple(s.get('modifiers',[]))
    expected={key(s) for s in gold['spans']}; actual={key(s) for s in predicted['spans']}
    raw=source.encode('utf-16-le')
    def describe(items):
        return [dict(start=a,end=b,tokenType=r,modifiers=list(m),text=raw[a*2:b*2].decode('utf-16-le')) for a,b,r,m in sorted(items)[:24]]
    return predicted,dict(metrics=metric.report(),missing=describe(expected-actual),unexpected=describe(actual-expected))


def code_regions(source, result):
    raw=source.encode('utf-16-le');language=None;regions=[]
    for span in result['spans']:
        role=span['tokenType']
        if role=='code-fence':language=None
        elif role=='code-language':language=raw[span['start']*2:span['end']*2].decode('utf-16-le').strip().lower()
        elif role=='embedded-code':
            regions.append(dict(start=span['start'],end=span['end'],infoWord=language));language=None
    return regions


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--device',default='mps')
    args=parser.parse_args()
    with using('markdown'):
        pack=LocalPack(checkpoint_path=args.checkpoint,device_name=args.device)
        aggregate=SpanMetrics(pack.checkpoint['schema']); displays=[]; natural=[]
        folder=REPOSITORY/'apps/playground/src/views/highlighter/examples/formats/markdown'
        for file in sorted(p for p in folder.iterdir() if p.suffix in {".md", ".markdown", ".mdown", ".mkd"}):
            source=file.read_bytes().decode('utf-8'); gold=label(source=source,profile='markdown')
            predicted,report=compare(pack,source,gold); aggregate.add(gold,predicted)
            expected=code_regions(source,gold);actual=code_regions(source,predicted)
            displays.append(dict(filename=file.name,sourceSha256=file_hash(file),predictedCodeRegions=dict(expected=expected,actual=actual,exact=expected==actual),**report))
            print(file.name,round(report['metrics']['exactSpan']['f1'],4),flush=True)
        snapshot=Path(pack.checkpoint['dataset']['path']).expanduser()
        records=[r for r in map(json.loads,(snapshot/'validation/documents.jsonl').read_text().splitlines()) if r['stream']=='natural']
        buckets = {}
        for record in records:
            buckets.setdefault((record['repository'], record['profile']), []).append(record)
        inspected = []
        while len(inspected) < min(10, len(records)):
            for bucket in buckets.values():
                if bucket and len(inspected) < 10:
                    inspected.append(bucket.pop(0))
        for r in inspected:
            source=r['source']; predicted,report=compare(pack,source,r['result'])
            natural.append({**{k:r[k] for k in ['repository','path','sourceGroup','contentHash']},**report})
            print(r['repository'],r['path'],round(report['metrics']['exactSpan']['f1'],4),flush=True)
        report=dict(checkpoint=str(args.checkpoint),checkpointHash=file_hash(args.checkpoint),checkpointEpoch=pack.checkpoint['epoch'],
                    purpose='Visible display probes and inspected natural validation only; not unseen test accuracy',
                    displayMetrics=aggregate.report(),displays=displays,naturalValidation=natural)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__': main()
