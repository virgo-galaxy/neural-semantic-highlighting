"""Bounded original instruction/CDATA/entity/attribute compositions after review."""
from pathlib import Path
import hashlib,json,random
from xml.sax.saxutils import escape,quoteattr
from training.shared.spec import PackSpec,file_hash
WORDS='amber birch cedar dawn estuary fern grove harbor iris jade kiln lake meadow nook orchard pebble river shore tulip vale'.split()
def main():
 root=PackSpec.open('xml').dataset_root/'sources/mixed-v1';files={}
 from packs.xml.labeling.label import label
 for depth in range(1,5):
  for count in range(1,6):
   for v in range(24):
    family=f'composition-{depth}-{count}';word=WORDS[(depth*5+count+v)%len(WORDS)];n=random.Random(711*depth+31*count+v).randrange(6,60)
    q=lambda t:quoteattr(str(t))
    for kind in ['xml','svg']:
     if kind=='xml':
      children=[]
      for j in range(count):
       text=f'{word} &lt;node&gt; original &amp; value &#65; end'
       literal=f'<![CDATA[When x < {n} && y > 0:\n  write("<{word} key=\'original\'>");\n  # literal &amp; text\n]]>'
       children.append(f'<record id={q(word+str(j))}>\n  <name>{text}</name>\n  <body>{literal}</body>\n  <flag/>\n</record>')
      inner='\n'.join(children)
      for d in range(depth):inner=f'<group{d} mode={q(word)}>\n'+inner+f'\n</group{d}>'
      root_name='records';attrs=' xmlns="urn:example:records" xmlns:m="urn:example:metadata" m:revision='+q(n)
     else:
      children=[]
      for j in range(count):
       children.append(f'<circle cx={q(n+j)} cy={q(n+3)} r={q(4+j)}>\n  <animate attributeName="opacity" values={q(f"0;{0.5+j/10};1")}\n           dur={q(str(j+1)+"s")} repeatCount="indefinite"/>\n</circle>')
      inner='\n'.join(children)+f'\n<text xml:lang="en">{word} &lt;shape&gt; &amp; &#x2728;</text>\n<style><![CDATA[\n .{word} {{ fill: #51a0f4; stroke-width: {n}; }}\n]]></style>'
      for d in range(depth):inner=f'<g id={q(word+str(d))} transform={q(f"rotate({n} 50 50)")}>\n'+inner+'\n</g>'
      root_name='svg';attrs=' xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"'
     source=f'<{root_name}{attrs}>\n<!-- Authored {word} composition -->\n'+inner+f'\n</{root_name}>\n'
     if v%3==1:source=f'<!DOCTYPE {root_name} PUBLIC "-//Example//DTD {word} source//EN" "https://example.test/{word}.dtd">\n'+source
     elif v%3==2:source=f'<!DOCTYPE {root_name} [<!ELEMENT {root_name} ANY>]>\n'+source
     if v%4 in {1,3}:source=f'<?{word}-source mode={q("original")} count={q(n)}?>\n'+source
     declarations=['<?xml version="1.0"?>','<?xml version=\'1.0\' encoding=\'UTF-8\'?>','<?xml version="1.0" encoding="UTF-8" standalone="yes"?>','']
     decl=declarations[v%4]
     if decl:source=decl+'\n'+source
     if v%5==2:source=source.replace('\n','\r\n')
     if v%13==4:source='\ufeff'+source
     label(source=source,document_kind=kind);raw=source.encode();p=root/family/f'{v:02}.{kind}';p.parent.mkdir(parents=True,exist_ok=True)
     if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve previous XML/SVG mixed task')
     if not p.exists():p.write_bytes(raw)
     files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original mixed XML/SVG compositions authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve original mixed license')
 p.write_bytes(license);lock=dict(format='nsh-xml-mixed-v1',generatorSha256=file_hash(Path(__file__)),families=20,files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve original mixed lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'files in 20 shared mixed families')
if __name__=='__main__':main()
