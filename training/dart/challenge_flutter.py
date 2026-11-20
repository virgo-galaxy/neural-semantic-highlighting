"""Visible Flutter framework probes with the frozen Dart model; no SDK/training."""
from pathlib import Path
import argparse,hashlib,json
from training.shared.spec import PackSpec,REPOSITORY,file_hash,using
from training.shared.golden import unmark
from training.shared.metrics import SpanMetrics
from training.shared.runtime import LocalPack
from packs.dart.labeling.label import label

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',default='auto');p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    spec=PackSpec.open('dart')
    with using('dart'):
        pack=LocalPack(pack_id='dart',device_name=args.device)
        displays=SpanMetrics(pack.checkpoint['schema']);goldens=SpanMetrics(pack.checkpoint['schema'])
        def review(source,expected):
            actual=pack.highlight(source=source,document_kind='dart');metric=SpanMetrics(pack.checkpoint['schema']);metric.add(expected,actual)
            def key(s):return s['start'],s['end'],s['tokenType'],tuple(s.get('modifiers',[]))
            g={key(x) for x in expected['spans']};a={key(x) for x in actual['spans']};raw=source.encode('utf-16-le')
            def describe(values):return [dict(start=x,end=y,text=raw[x*2:y*2].decode('utf-16-le'),tokenType=r,modifiers=list(m)) for x,y,r,m in sorted(values)]
            return dict(source=source,result=actual,metrics=metric.report(),exactIncludingModifiers=a==g,missing=describe(g-a),unexpected=describe(a-g)),actual
        cases=[]
        for case in json.loads((spec.directory/'fixtures/flutter-golden.json').read_text()):
            gold=unmark(case['markedSource']);row,actual=review(gold['source'],gold);goldens.add(gold,actual);cases.append(dict(id=case['id'],**row))
        display=[]
        for path in sorted((REPOSITORY/'apps/playground/src/views/highlighter/examples/code/flutter').glob('*.dart')):
            source=path.read_bytes().decode('utf-8');expected=label(source=source);row,actual=review(source,expected);displays.add(expected,actual);display.append(dict(filename=path.name,sourceSha256=file_hash(path),**row))
        report=dict(purpose='Visible independent Flutter framework probes; not unseen test or SDK compilation',canonicalDocumentKind='dart',modelSha256=file_hash(spec.directory/'model/model.pt'),golden=dict(fixtureSha256=file_hash(spec.directory/'fixtures/flutter-golden.json'),aggregate=goldens.report(),exactCases=sum(r['exactIncludingModifiers'] for r in cases),cases=cases),display=dict(aggregate=displays.report(),cases=display),sdkInstalled=False,trainingPerformed=False)
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        for row in display:print(row['filename'],round(row['metrics']['exactSpan']['f1']*100,2))
        print('Visible aggregate',round(report['display']['aggregate']['exactSpan']['f1']*100,2),'F1; neural Golden',report['golden']['exactCases'],'/',len(cases))
if __name__=='__main__':main()
