"""Original shared XML/SVG tree families; never reads Golden or display files."""
from pathlib import Path
from xml.sax.saxutils import escape,quoteattr
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
WORDS='aspen brook cypress delta elm forest glade heath island juniper kelp lotus mist north ocean pine quartz reed sage thyme'.split()
def main():
 root=PackSpec.open('xml').dataset_root/'sources/curriculum-v1';files={}
 from packs.xml.labeling.label import label
 for depth in range(1,6):
  for siblings in range(1,9):
   family=f'tree-{depth}-{siblings}'
   for variant in range(24):
    word=WORDS[(depth*7+siblings+variant)%len(WORDS)];n=random.Random(8721+depth*751+siblings*31+variant).randrange(5,90)
    quote=lambda x:quoteattr(str(x))if variant%2 else "'"+str(x).replace('&','&amp;').replace("'",'&apos;')+"'"
    for kind in ['xml','svg']:
     if kind=='xml':
      children=[f'<entry index={quote(i)} active={quote("true"if i%2 else"false")}><label>{word} &amp; item {i}</label><value unit={quote("px")}>{n+i}</value></entry>'for i in range(siblings)]
      inner='\n'.join(children)+f'\n<literal><![CDATA[if (value < {n} && ready) {{ use("<{word}>"); }}]]></literal>'
      for d in range(depth):inner=f'<section{d} name={quote(word+str(d))}>\n'+inner+f'\n</section{d}>'
      source=f'<document xmlns={quote("urn:example:"+word)} xmlns:m={quote("urn:example:meta")} m:revision={quote(n)}>\n<!-- Original {word} tree -->\n'+inner+'\n</document>\n'
     else:
      children=[f'<path id={quote(word+str(i))} d={quote(f"M{n+i} 4L{i+8} {n}h12z")} fill={quote("currentColor")} stroke-width={quote(1+i%3)}/>'for i in range(siblings)]
      inner='\n'.join(children)+f'\n<text x={quote(n)} y={quote(n+4)}>{word} &amp; color &#x2728;</text>\n<style><![CDATA[.{word} {{ fill: #3588aa; stroke: none; }}]]></style>'
      for d in range(depth):inner=f'<g transform={quote(f"translate({d+1} {n})")} opacity={quote("0.8")}>\n'+inner+'\n</g>'
      source=f'<svg xmlns={quote("http://www.w3.org/2000/svg")} xmlns:xlink={quote("http://www.w3.org/1999/xlink")} viewBox={quote("0 0 100 100")} role={quote("img")}>\n<!-- Original {word} vector -->\n'+inner+'\n</svg>\n'
     if variant%7==1:source='<?source-preview mode="literal"?>\n'+source
     if variant%8==2:source='<!DOCTYPE '+('document'if kind=='xml'else'svg')+' SYSTEM "https://example.test/never-fetched.dtd">\n'+source
     if variant%6==0:source='<?xml version="1.0" encoding="UTF-8"?>\n'+source
     if variant%4==3:source=source.replace('\n','\r\n')
     if variant%11==5:source='\ufeff'+source
     label(source=source,document_kind=kind);raw=source.encode();p=root/family/f'{variant:02}.{kind}';p.parent.mkdir(parents=True,exist_ok=True)
     if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve previous XML/SVG task')
     if not p.exists():p.write_bytes(raw)
     files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original XML/SVG tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve original XML/SVG license')
 p.write_bytes(license);lock=dict(format='nsh-xml-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=40,files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve original XML/SVG lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'files in 40 shared XML/SVG families')
if __name__=='__main__':main()
