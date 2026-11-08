"""Original short literal-boundary tasks; never consume Golden or display probes."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash

TEMPLATES={
 'quoted-select':"SELECT {literal} AS description FROM inventory;\n",
 'quoted-insert':"INSERT INTO messages (body, priority) VALUES ({literal}, {n});\nSELECT id FROM messages;\n",
 'quoted-update':"UPDATE messages SET body = {literal} WHERE id = {n};\nSELECT body FROM messages;\n",
 'quoted-case':"SELECT CASE WHEN active THEN {literal} ELSE 'pending' END AS description FROM jobs;\n",
 'quoted-call':"SELECT LENGTH({literal}) AS size FROM messages WHERE id = {n};\n",
 'quoted-cte':"WITH notes AS (SELECT {literal} AS body) SELECT body FROM notes;\n",
 'routine-sql':"CREATE FUNCTION {fn}(p_input integer) RETURNS integer LANGUAGE sql AS {body};\nSELECT {fn}({n});\n",
 'routine-language-last':"CREATE FUNCTION {fn}(p_input integer) RETURNS integer AS {body} LANGUAGE sql;\nSELECT {fn}({n});\n",
 'routine-do':"DO {body};\nSELECT name FROM inventory WHERE id = {n};\n",
 'routine-replace':"CREATE OR REPLACE FUNCTION {fn}(p_input integer) RETURNS integer LANGUAGE sql AS {body};\n",
 'typed-select':"SELECT $1::integer, name FROM inventory WHERE id = $2::bigint;\n",
 'typed-compare':"SELECT name FROM inventory WHERE price > $1::numeric AND active = $2::boolean;\n",
 'typed-update':"UPDATE inventory SET price = $1::decimal WHERE id = $2::integer;\n",
 'typed-function':"SELECT SUM(price), CAST($1 AS integer) FROM inventory WHERE id > $2::integer;\n",
}

def main():
 root=PackSpec.open('sql').dataset_root/'sources/literals-v1';files={}
 for family,template in TEMPLATES.items():
  profiles=['postgres'] if family.startswith(('routine-','typed-')) else ['postgres','oracle']
  for profile in profiles:
   for i in range(48):
    prefix=['','-- Literal boundary task\n','\n','/* Source fragment */\n'][(i//12)%4]
    indent=['','  ','    '][i%3]
    words=["it's already prepared",'a different message','星空 🌌 report',"name='value'; -- body text"][i%4]
    if profile=='oracle':
     left,right=[('[',']'),('(',')'),('{','}'),('<','>'),('!','!'),('#','#')][(i//4)%6]
     literal="q'"+left+words+right+"'"
    else:
     tag=['$$','$text$','$note$','$message$'][(i//4)%4];literal=tag+words+tag
    tag=['$$','$task$','$procedure$','$code$'][(i//3)%4]
    body=tag+'\n'+indent+'SELECT p_input + '+str(i+11)+';\n'+tag
    source=prefix+template.format(literal=literal,body=body,fn=['adjust_price','increase_limit','normalize_count','compute_score'][i%4],n=i+11)
    if i%7==3:source=source.replace('\n','\r\n')
    files[f'{profile}/{family}/{i:02}.sql']=source.encode()
 files['LICENSE']=b'Original private neural-semantic-highlighting SQL boundary tasks. No additional license grant.\n'
 for name,raw in files.items():
  path=root/name
  if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve original source')
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 lock={'format':'nsh-sql-original-literals-v1','generatorHash':file_hash(Path(__file__)),'files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()}}
 target=root/'source.lock.json'
 if target.exists() and json.loads(target.read_text())!=lock:raise ValueError('Preserve source lock')
 target.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'original boundary tasks')
if __name__=='__main__':main()
