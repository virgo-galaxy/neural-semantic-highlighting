"""Mixed INI contexts following actual validation/display range-error review."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
TEMPLATES={
'versions':'[package @W@]\nversion=4.5.@N@\nrequires_python=>=3.12\nrequirements=\n  library>=2.0\n  shared~=1.4\n[flags]\nready=true\nsize=@N@',
'package-dir':'[metadata]\nname=@W@\n[options]\npackage_dir=\n  = libsrc\n  extra = shared\npython_requires=>=3.12\ninclude_package_data=True\n[options.packages.find]\nwhere=libsrc\ncount=@N@',
'embedded-assignments':'[document]\nname=@W@\nbody=opening\n  cache=true is text\n  host=server:@N@\n  [section-looking text]\n  limit=@N@\nend=finished\n[status]\nready=yes',
'commands':'[tasks @W@]\nrun=\n  echo "${WORKSPACE}"\n  runner --check src --limit @N@\n  printf "%s" "$HOME"\nargs=one, two, three\n[environment]\nPATH=/bin:/usr/bin\nsecure=off',
'raw-commas':'name=@W@\n[environments]\nlist=py312, py313, current\npaths=HOME, PATH, TMPDIR\ncommand=checker inspect source\nlimit=@N@\n[output]\nformat=text\ninclude=src, docs\nready=true',
'url-values':'[links]\nproject=@W@\napi=https://example.test:8080/@W@?x=@N@&ready=true#part\nroot=C:\\home\\@W@\\notes\nlabels=one; two; three\nmessage=word # literal data\n[flags]\nenabled=no',
'quoted-values':'[display "@W@.page"]\nmessage="one # two; three = four"\npattern=\'^\\w+\\d+$\'\nquote="true"\nversion="4.@N@"\nwidth=@N@\n[style @W@]\nfont=monospace\nselected=YES',
'multiple-headers':'root=true\n[tool.@W@]\nvalue=one\n[[ab]*.source]\nindent_size=@N@\n[*.{js,ts,jsx,tsx}]\ncharset=utf-8\n[build "@W@.release"]\nmode=production\ncache=false',
'continuation-lists':'[includes]\nname=@W@\nfiles=\n  # full line comment\n  alpha, beta\n  ; disabled item\n\n  gamma>=@N@\n  [literal glob]\nmode=active\n[extra]\ncount=@N@',
'empty-flags':'[features]\nname=@W@\nflag\nempty=\nblank:\n[service]\nport=@N@\nsecure=yes\n[service]\naddress=127.0.0.1\nmode=replace',
'bool-number-values':'# @W@ scalar display\n[limits]\ncount=@N@\nratio=-1.75e+2\nmask=0xAB\n[features]\ncache=ON\ndebug=False\nquoted="no"\ntext=4.5.6\nunits=20ms\nports=80, 443',
'continued-expressions':'[expressions]\nname=@W@\nitems=first\n  %(root)s/@W@\n  ${PREFIX}/src\n  key: value # retained\n  if count >= @N@ then return\n  true\n[options]\nlimit=@N@\nready=false'
}
WORDS='amber birch coral dune ember fennel grove hazel iris jade kestrel linen maple nettle olive pebble quill river sorrel tundra'.split()
def main():
 root=PackSpec.open('ini').dataset_root/'sources/curriculum-mixed-v1';files={}
 from packs.ini.labeling.label import label
 for index,(family,template)in enumerate(TEMPLATES.items()):
  for variant in range(24):
   source=template.replace('@W@',WORDS[(index+variant)%len(WORDS)]).replace('@N@',str(random.Random(9696+index*101+variant).randrange(3,90)))+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   if variant%13==3:source='\ufeff'+source
   label(source=source)
   raw=source.encode();p=root/family/f'{variant:02}.ini';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve previous INI mixed task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original INI mixed tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve original INI license')
 p.write_bytes(license);lock=dict(format='nsh-ini-mixed-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve original INI mixed lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'mixed files in',len(TEMPLATES),'families')
if __name__=='__main__':main()
