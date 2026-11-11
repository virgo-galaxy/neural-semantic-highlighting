"""Separate mixed JSON-family tasks after observed string/comment coverage gaps."""
from pathlib import Path
import json,hashlib,random
from training.shared.spec import PackSpec,file_hash
FAMILIES=['service-registry','log-pipeline','document-assets','certificates','source-maps','keybindings','webhooks','editor-filters','translations','deployment-matrix','package-scripts','documentation-content']
WORDS='amber basalt coral dune estuary fir glacier harbor indigo jasper lagoon meadow opal pebble redwood spruce terra valley wheat'.split()
def document(family,word,n):
 quoted='The '+word+' record says "ready"; keep \\ separators and // /* literal markers.'
 values={
 'service-registry':{'services':[{'name':word,'address':'https://'+word+'.example.test/api','notes':quoted,'headers':{'x-display':'"'+word+'"'}}],'ports':[n,n+1000],'healthy':True,'owner':None},
 'log-pipeline':{'format':'[%s] "'+word+'"\t%message','filters':[{'kind':'pattern','pattern':'^\\w+\\d+\\s*$','enabled':True}],'sinks':[{'url':'https://logs.example.test/'+word,'batch':n,'compress':False}]},
 'document-assets':{'documents':{word:{'body':quoted,'mime':'text/plain','visible':False}},'order':[word],'revision':n,'cache':{'ttl':n*2,'enabled':True}},
 'certificates':{'certificates':[{'subject':word,'pem':'--- BEGIN '+word+' ---\nDATA\\DATA\n--- END ---'}],'trust':{'roots':['local','team'],'verify':True},'timeout':n,'fallback':None},
 'source-maps':{'version':3,'sources':[word+'.ts','lib.ts'],'sourcesContent':['export const '+word+' = "quoted";','/* source */ const pattern = /\\w+/;'],'mappings':'AAAA,CAAC','names':[word],'metadata':None},
 'keybindings':{'bindings':[{'keys':['ctrl-'+word[0],'alt-enter'],'command':'open("'+word+'")','when':'editor && kind == "'+word+'"'}],'scope':{'terminal':False,'editor':True},'priority':n,'excluded':[]},
 'webhooks':{'url':'https://hooks.example.test/'+word,'events':['document.saved','entry.updated'],'body':{'template':'${record.'+word+'}','nested':'{"message":"'+word+'","ok":true}'},'retry':[n,n*2,n*3],'token':None},
 'editor-filters':{'filters':{'path\\'+word:'C:\\sources\\'+word,'quoted"'+word:quoted},'rules':[{'include':['**/*.ts','**/*.json'],'enabled':True}],'version':n,'fallback':False,'commentText':'// filter '+word+' /* raw data */'},
 'translations':{'locale':word,'messages':{'label':'Choose "'+word+'"','multiline':'One\nTwo\nThree','control':'Tab\tand carriage\rreturn'},'counts':[1,n],'formats':{'date':'yyyy-MM-dd','enabled':True},'other':None},
 'deployment-matrix':{'matrix':[{'region':word,'commands':['echo "ready"','printf "\\n"'],'weights':[n/100,0.5],'enabled':True}],'secrets':{'provider':'${vault.'+word+'}','required':False},'output':None},
 'package-scripts':{'scripts':{'serve':'node -e "console.log(\\"'+word+'\\")"','clean':'echo "C:\\cache\\'+word+'"'},'arguments':['--message',quoted],'timeouts':{'start':n,'stop':n+1},'watch':True,'files':[]},
 'documentation-content':{'article':{'title':word,'body':('Entry "'+word+'"; paths \\ and ${literal}; // still data.\n')*14,'draft':True},'sections':[{'id':n,'anchors':[word,'extra']}],'published':None},
 }
 return values[family]
def main():
 root=PackSpec.open('json').dataset_root/'sources/curriculum-mixed-v1';files={}
 for index,family in enumerate(FAMILIES):
  for v in range(24):
   word=WORDS[(v+index)%len(WORDS)];value=document(family,word,random.Random(9401+index*71+v).randrange(3,80));source=json.dumps(value,ensure_ascii=v%5==0,indent=None if v%6==0 else 2)
   for profile in ['json','jsonc']:
    text=source
    if profile=='jsonc':
     lines=['Configuration notes for '+family+' / '+word+'.','A quoted "identifier", // text and {braces} here are comment data.','Do not execute '+word+' commands or parse example strings.']
     if v%3==0:lines+=['Reference '+word+' includes paths \\ and quoted text "raw".']*6
     text='/*\n  '+'\n  '.join(lines)+'\n*/\n'+text
     if v%2==0:
      at=text.rfind('}');text=text[:at].rstrip()+', // Final configuration entry.\n'+text[at:]
     else:text+=' // Retain this source exactly.'
    text+='\n'
    if v%4==1:text=text.replace('\n','\r\n')
    raw=text.encode();p=root/profile/('mixed-'+family)/(f'{v:02}.'+profile);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve prior mixed task')
    if not p.exists():p.write_bytes(raw)
    files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original mixed JSON/JSONC tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists() and p.read_bytes()!=license:raise ValueError('Preserve original mixed license')
 p.write_bytes(license);lock=dict(format='nsh-json-mixed-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(FAMILIES),profiles=['json','jsonc'],files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve previous mixed lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'mixed files;',len(FAMILIES),'shared source families')
if __name__=='__main__':main()
