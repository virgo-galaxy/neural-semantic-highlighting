"""Original JSON/JSONC task families, isolated from Golden and display examples."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
FAMILIES=['package','scripts','dependencies','workspace','exports','compiler','paths','settings','launch','tasks','extensions','api-list','api-error','pagination','schema','schema-union','geojson','theme','design-tokens','localization','permissions','feature-flags','event','telemetry','manifest','nested-arrays','mixed-values','numbers','numeric-map','escaped-paths','escaped-keys','quoted-content','unicode','long-text','deep-nesting','repeated-records','primitive-string','primitive-number','primitive-boolean','primitive-null']
WORDS='alder birch cedar daisy ember frost granite hazel iris jade kelp lake maple nectar ocean pearl quartz river sage timber umber violet willow xenon yarrow zinc'.split()
def document(family,v,rng):
 word=WORDS[v%len(WORDS)];n=rng.randrange(2,90);text=word+' 🌌'
 values={
 'package':{'name':'@demo/'+word,'version':f'1.{v}.0','private':True,'description':text,'license':'MIT'},
 'scripts':{'scripts':{'dev':'vite --host 127.0.0.1','check':'tsc --noEmit','build':'vite build'},'engines':{'node':'>=24'},'sideEffects':False},
 'dependencies':{'dependencies':{word:'^2.0.0','util-'+word:'~1.0.0'},'devDependencies':{'typescript':'^6.0.0'},'optionalDependencies':{'native-'+word:'1.0.0'}},
 'workspace':{'packages':['apps/*','packages/*',word+'/*'],'catalog':{'core':'workspace:*'},'overrides':{'native':'1.2.0'},'linkWorkspacePackages':True},
 'exports':{'type':'module','exports':{'.':{'types':'./dist/index.d.ts','import':'./dist/index.js'},'./'+word:'./dist/'+word+'.js'},'files':['dist'],'main':'./dist/index.js'},
 'compiler':{'compilerOptions':{'strict':True,'target':'ES2022','module':'ESNext','lib':['DOM','ES2022']},'include':['src/'+word+'/**/*.ts'],'exclude':['dist']},
 'paths':{'extends':'./base.json','compilerOptions':{'baseUrl':'.','paths':{'@'+word+'/*':['./src/*'],'core':['./packages/core/index.ts']}},'references':[{'path':'./lib'}]},
 'settings':{'editor.tabSize':2,'editor.formatOnSave':True,'files.exclude':{'**/dist':True},'workbench.colorTheme':word,'search.exclude':{'**/cache':True}},
 'launch':{'version':'0.2.0','configurations':[{'name':word,'type':'node','request':'launch','program':'${workspaceFolder}/index.js','args':['--port',str(n)]}]},
 'tasks':{'version':'2.0.0','tasks':[{'label':word,'type':'shell','command':'npm run build','group':{'kind':'build','isDefault':True},'problemMatcher':['$tsc']}]},
 'extensions':{'recommendations':['demo.'+word,'demo.core'],'unwantedRecommendations':['legacy.syntax'],'metadata':{'source':'team','count':n}},
 'api-list':{'data':[{'id':n,'name':word,'active':True},{'id':n+1,'name':'next','active':False}],'meta':{'total':n+2,'cursor':None}},
 'api-error':{'error':{'code':'INVALID_'+word.upper(),'message':'Request rejected','details':[{'field':'email','reason':'missing'}]},'requestId':'req_'+word,'retryable':False},
 'pagination':{'items':[word,'second','third'],'page':v+1,'pageSize':n,'hasNext':True,'next':{'cursor':'cursor-'+word,'limit':n}},
 'schema':{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'https://example.test/'+word,'type':'object','properties':{'title':{'type':'string'},'count':{'type':'integer','minimum':0}},'required':['title'],'additionalProperties':False},
 'schema-union':{'$defs':{'item':{'type':'string','enum':[word,'other']}},'oneOf':[{'$ref':'#/$defs/item'},{'type':'null'}],'description':'Union '+word},
 'geojson':{'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[n/10,-n/4]},'properties':{'name':word,'visible':True}}]},
 'theme':{'name':word,'colors':{'editor.background':'#10141c','editor.foreground':'#edf1f7'},'tokenColors':[{'scope':['string','comment'],'settings':{'foreground':'#abcd12'}}]},
 'design-tokens':{'color':{'brand':{'$type':'color','$value':'#1287ef'},'surface':{'$value':'{color.brand}'}},'spacing':{'small':{'$type':'dimension','$value':n}},'$description':word},
 'localization':{'en':{'greeting':'Hello '+word,'count':'{count} items'},'zh':{'greeting':'你好 🌌','count':'共 {count} 个'},'fallback':None},
 'permissions':{'role':word,'permissions':[{'resource':'docs','actions':['read','write']},{'resource':'settings','actions':['read']}],'enabled':True,'expires':None},
 'feature-flags':{'flags':{'new-'+word:{'enabled':True,'rollout':n/100,'audiences':['beta']}},'defaults':{'enabled':False},'updatedAt':'2026-01-01'},
 'event':{'type':'document.'+word,'payload':{'documentId':'doc_'+str(n),'changes':[{'op':'replace','path':'/title','value':word}]},'timestamp':n*1000},
 'telemetry':{'metrics':[{'name':word,'value':n/3,'labels':{'region':'east','status':'ok'}}],'interval':n,'enabled':False,'sample':None},
 'manifest':{'name':word,'short_name':word[:3],'start_url':'/','display':'standalone','icons':[{'src':'/icon.svg','sizes':'any','type':'image/svg+xml'}],'theme_color':'#123456'},
 'nested-arrays':[[word,n,None],[True,False,[1,2,3]],{'rows':[[1,n],[n,2]]}],
 'mixed-values':{'values':[word,n,n/10,True,False,None,{'nested':[word]}],'emptyObject':{},'emptyArray':[]},
 'numbers':{'integer':n,'negative':-n,'fraction':n/100,'scientific':n*1e12,'small':n*1e-12,'zero':0},
 'numeric-map':{str(n):{'value':n,'next':None},str(n+1):{'value':-n,'next':str(n)}},
 'escaped-paths':{'windows':'C:\\workspace\\'+word+'\\src','network':'\\\\server\\share','url':'https://example.test/'+word+'?x=1&y=2','separator':'\t\n\r'},
 'escaped-keys':{'quoted"'+word:'line\nbreak','path\\'+word:'\u0001control','slash/key':'a/b','':word},
 'quoted-content':{'commentText':'// not a comment /* still string */','code':'const '+word+' = {"ready": true};','template':'${workspaceFolder}/'+word,'regex':'^\\w+\\d+$'},
 'unicode':{'名称':word,'message':'星空 🌌 café é','emoji':'👩🏽‍💻','active':True,'count':n},
 'long-text':{'title':word,'content':('Article '+word+' with punctuation {} [] : , // /* and 🌌. ')*18,'metadata':{'length':n,'published':True}},
 'deep-nesting':{'workspace':{'projects':[{'name':word,'modules':{'core':{'options':{'strict':True,'level':n,'tags':[word]}}}}]}},
 'repeated-records':[{'key':word+str(i),'value':n+i,'options':{'enabled':i%2==0}} for i in range(5)],
 'primitive-string':'Text '+word+' with "quotes" and \\ paths 🌌',
 'primitive-number':n/7,
 'primitive-boolean':v%2==0,
 'primitive-null':None,
 }
 value=values[family];source=json.dumps(value,ensure_ascii=(v%5==0),indent=None if v%4==0 else 2,allow_nan=False)
 if family=='numbers' and v%3==0:source='{"negativeZero":-0,"exponent":-1.25e+03,"fraction":0.00001,"large":123456789012345678901234567890}'
 return source,value

def main():
 root=PackSpec.open('json').dataset_root/'sources/curriculum-v1';files={}
 for index,family in enumerate(FAMILIES):
  for v in range(24):
   source,value=document(family,v,random.Random(8259+index*97+v))
   for profile in ['json','jsonc']:
    text=source
    if profile=='jsonc':
     text=('// '+family+' configuration\n' if v%2==0 else '/* '+family+' configuration 🌌 */\n')+text
     if isinstance(value,(dict,list)) and value and v%3==0:
      at=text.rfind('}' if isinstance(value,dict) else ']');text=text[:at].rstrip()+',\n'+text[at:]
     if v%3==1:text+=' // End of '+family
    text+='\n'
    if v%4==1:text=text.replace('\n','\r\n')
    raw=text.encode();p=root/profile/family/(f'{v:02}.'+profile);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve prior JSON-family task')
    if not p.exists():p.write_bytes(raw)
    files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original JSON/JSONC tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists() and p.read_bytes()!=license:raise ValueError('Preserve original curriculum license')
 p.write_bytes(license);lock=dict(format='nsh-json-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(FAMILIES),profiles=['json','jsonc'],files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve original curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'files;',len(FAMILIES),'shared source families;',len(FAMILIES)*24,'per profile')
if __name__=='__main__':main()
