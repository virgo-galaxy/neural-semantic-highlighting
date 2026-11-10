"""Review the unchanged Dart model on pinned Flutter applications; no SDK/training."""
from pathlib import Path
from collections import defaultdict
import argparse,hashlib,json
from training.shared.spec import PackSpec,file_hash,using
from training.shared.encoding import Schema,encode
from training.shared.metrics import SpanMetrics
from training.shared.runtime import LocalPack
from packs.dart.labeling.label import label

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device',default='auto',choices=['auto','cpu','mps','cuda'])
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();spec=PackSpec.open('dart')
    config=json.loads((spec.directory/'dataset/flutter-examples.json').read_text())
    root=spec.dataset_root/'sources'/config['id'];lock=json.loads((root/'source.lock.json').read_text())
    if lock['upstream']!=config:raise ValueError('Flutter capture configuration differs')
    for name,row in lock['files'].items():
        if file_hash(root/name)!=row['sha256']:raise ValueError('Flutter capture hash differs')
    with using('dart'):
        pack=LocalPack(pack_id='dart',device_name=args.device);schema=Schema.load(spec.schema_path)
        # Match exact, lexical and normalized-shape fingerprints against all prior
        # Gold, keeping this new review distinct from the historical test score.
        pointer=json.loads((spec.dataset_root/'current-gold.json').read_text())
        folder=spec.dataset_root/pointer['directory'];seen=defaultdict(list)
        for line in (folder/'labeled-sample.jsonl').read_text().splitlines():
            r=json.loads(line);encoded=encode(r,schema)
            for kind,digest in [('exact',r['contentHash']),('lexical',encoded.normalized_hash),('shape',encoded.shape_hash)]:
                seen[(kind,digest)].append(dict(repository=r['repository'],path=r['path'],sourceGroup=r['sourceGroup']))
        total=SpanMetrics(pack.checkpoint['schema']);novel=SpanMetrics(pack.checkpoint['schema']);families={}
        rows=[];rejected=[]
        for item in config['files']:
            if item['license']:continue
            source=(root/item['path']).read_bytes().decode('utf-8')
            try:
                expected=label(source=source)
                encoded=encode(dict(source=source,documentKind='dart',result=expected,contentHash=lock['files'][item['path']]['sha256']),schema)
            except ValueError as error:
                rejected.append(dict(path=item['path'],error=str(error)));continue
            actual=pack.highlight(source=source,document_kind='dart')
            metric=SpanMetrics(pack.checkpoint['schema']);metric.add(expected,actual);total.add(expected,actual)
            family=item['path'].split('/')[0]
            if family not in families:families[family]=SpanMetrics(pack.checkpoint['schema'])
            families[family].add(expected,actual)
            matches={kind:seen.get((kind,digest),[]) for kind,digest in [('exact',lock['files'][item['path']]['sha256']),('lexical',encoded.normalized_hash),('shape',encoded.shape_hash)]}
            if not any(matches.values()):novel.add(expected,actual)
            def key(s):return s['start'],s['end'],s['tokenType']
            g={key(s) for s in expected['spans']};a={key(s) for s in actual['spans']};raw=source.encode('utf-16-le')
            def describe(values):return [dict(start=x,end=y,text=raw[x*2:y*2].decode('utf-16-le'),tokenType=r) for x,y,r in sorted(values)]
            rows.append(dict(path=item['path'],family=family,source=source,contentHash=lock['files'][item['path']]['sha256'],metrics=metric.report(),priorGoldMatches=matches,missing=describe(g-a),unexpected=describe(a-g)))
        report=dict(purpose='New Flutter application review using the already selected Dart weights; not the historical held-out test or SDK certification',model=spec.directory.joinpath('model/model.json').as_posix(),modelSha256=file_hash(spec.directory/'model/model.pt'),device=pack.device.type,source=config,aggregate=total.report(),nonmatchingPriorGold=novel.report(),families={k:m.report() for k,m in families.items()},cases=rows,rejected=rejected,trainingPerformed=False,sdkInstalled=False)
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        print('Flutter applications:',len(rows),'accepted,',len(rejected),'rejected; F1',round(report['aggregate']['exactSpan']['f1']*100,2),'macro',round(report['aggregate']['exactSpanMacroF1']*100,2))
        print('Nonmatching prior Gold:',report['nonmatchingPriorGold']['documents'])
        for family,metric in report['families'].items():print(family,round(metric['exactSpan']['f1']*100,2))
if __name__=='__main__':main()
