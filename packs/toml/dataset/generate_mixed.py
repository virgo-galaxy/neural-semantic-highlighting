"""Mixed configuration contexts following validation/display string-boundary review."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
TEMPLATES={
'paragraph':'[metadata]\nname="@W@"\nsummary="""\nDocumentation for @W@ with "words" and # source data.\nSeveral original lines are preserved without parsing.\n"""\nversion=@N@\noptions={draft=false,tags=["notes","preview"]}',
'shell-table':"[[jobs]]\nname='@W@'\nscript='''\n#!/usr/bin/env bash\n# A script comment inside a TOML string\nvalue=@N@\necho \"${value}\"\n'''\nenabled=true\n[[jobs]]\nname='archive'\nscript='echo later'",
'json-table':"[request.@W@]\nheaders={accept='application/json'}\npayload='''\n{\"active\": false, \"items\": [@N@, 2]}\n'''\n[response]\nstatus=@N@\nlabels=['json','plain']",
'markup-list':"name='@W@'\ncontent=['''\n<main data-id=\"@N@\">\n  <!-- literal # content -->\n  <p>@W@</p>\n</main>\n''', 'fallback']\n[page]\nready=true",
'inline-text':'name="@W@"\nrender={\n title="sample",\n source="""\nA @W@ passage with # characters and \\"quotes\\".\nSecond line has {braces}, @N@ and [square brackets].\n""",\n enabled=true,\n}\nlimit=@N@',
'array-text':'[[translations]]\nlocale="@W@"\nmessages=["""\nFirst # original message.\nIt contains "quoted" data and ${names}.\n""", """\nSecond @W@ message with @N@.\n"""]\nreviewed=false',
'closing-comment':"[article]\nlabels=['@W@','source']\nbody='''\nThe @W@ source has # notes and \"values\".\nDo not treat the following data as syntax: x=@N@\n''' # comment after closing delimiter\nactive=true\nlimits={min=@N@,max=100}",
'continuation-text':'[notifications.@W@]\nport=@N@\ntext="""A @W@ message \\\n    with an escaped \\"word\\" and \\\n    a final original line."""\n[notifications.backup]\ntext="short"\nflags=[true,false]',
'quoted-numeric':'["@W@.settings"]\n"count.limit"=@N@\n"two words"=true\n["@W@.settings"."paths.root"]\n"1.23"="./@W@"\n"false"=["yes","no"]\n[["@W@.settings".items]]\n"id.value"=@N@',
'number-context':'# @W@ limits\n[metrics]\nvalues=[+9,-1.25e+3,inf,-inf,nan,+nan,0o77,0b101,0xff]\nlimits={min=-@N@,max=+@N@}\n[release]\ncreated=2026-10-12 16:20:00.75\nstart=08:15\nactive=true',
'escape-context':'[document."@W@.page"]\n"escaped.name"="slash\\\\ quote\\\" unicode\\xE9\\e"\n[document."@W@.page".release]\nwhen=2026-10-12T08:30Z\ncount=@N@\nrows=[{id=@N@,label="@W@"}]',
'literal-chain':"[tasks.@W@]\nargs=['verbose','source']\ncommands=['''\n# first literal command\nprintf '%s' \"$PATH\"\n''', '''\n# second literal command\nmessage=\"@W@\"\ncount=@N@\n''']\nenabled=false\n[settings]\nlimit=@N@"
}
WORDS='amber birch coral dune ember fennel grove hazel iris jade kestrel linen maple nettle olive pebble quill river sorrel tundra'.split()
def main():
 root=PackSpec.open('toml').dataset_root/'sources/curriculum-mixed-v1';files={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   source=template.replace('@W@',WORDS[(index+variant)%len(WORDS)]).replace('@N@',str(random.Random(3434+index*101+variant).randrange(3,90)))+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   from packs.toml.labeling.label import label
   label(source=source)
   raw=source.encode();p=root/family/f'{variant:02}.toml';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve previous TOML mixed task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original TOML mixed tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists() and p.read_bytes()!=license:raise ValueError('Preserve original license')
 p.write_bytes(license);lock=dict(format='nsh-toml-mixed-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve original mixed lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'mixed files in',len(TEMPLATES),'families')
if __name__=='__main__':main()
