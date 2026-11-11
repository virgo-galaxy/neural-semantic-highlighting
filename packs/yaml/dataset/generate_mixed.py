"""Separate mixed block/anchor families after real YAML validation review."""
from pathlib import Path
import json,hashlib,random
from training.shared.spec import PackSpec,file_hash
TEMPLATES={
'mixed-folded-literal':'title: @WORD@\nsummary: >-\n  A @WORD@ service uses "quotes" and # characters.\n  A second source line stays within this scalar.\npayload: |-\n  {"trace":"@WORD@","count":@N@,"valid":true}\nready: true\nports: [@N@, 8080]',
'mixed-ci-blocks':'jobs:\n  @WORD@:\n    env: {MODE: preview, LIMIT: "@N@"}\n    steps:\n      - name: Prepare\n        run: |-\n          printf "%s" "${PROJECT}"\n          # this is literal source\n          count=@N@\n      - name: Report\n        run: >-\n          echo "@WORD@ ready"\n          && echo "${count}"\n        continue-on-error: false',
'mixed-configmap':'items:\n  - name: @WORD@\n    content: |2- # Config payload\n      enabled: false\n      value: "@WORD@"\n      [null, true, @N@]\n    attributes: {region: east, active: true}\nrevision: @N@',
'mixed-chomping':'literal: |-\n  @WORD@ \\path\\source\n  # indented data\nkeep: |+\n  quoted "@WORD@" data\n\nfolded: >-\n  first @WORD@ line\n  second @WORD@ line\nlast: {count: @N@, value: null}',
'mixed-scalar-anchor':'commands:\n  base: &@NAME@ |-\n    echo "@WORD@"\n    key: false\n    # literal line\n  preview: *@NAME@\n  release: >-\n    printf "@WORD@ %s"\n    "${WORKSPACE}"\nsettings: {count: @N@, enabled: true}',
'mixed-tagged-blocks':'template: !Sub |-\n  arn:example:${Region}:@WORD@\n  # tag metadata does not execute this content\ndetails:\n  settings: &@NAME@ !Settings\n    title: @WORD@\n    attempts: @N@\n  copy: *@NAME@\nmessage: >-\n  A "tagged" @WORD@ description.\n  Preserve the original source range.',
'mixed-block-boundary':'before: [@WORD@, @N@, false]\nscript: |2- # Only this is a YAML comment\n  echo "@WORD@"\n  # This remains literal content\n  "quoted": [true, false]\n# An actual outer comment\nafter: {enabled: true, name: @WORD@}\ntext: >-\n  Last paragraph for @WORD@.\n  Two physical lines.',
'mixed-scalar-sequence':'records:\n  - |\n    {"name":"@WORD@","value":@N@}\n    # raw string content\n  - >-\n    A @WORD@ paragraph\n    continued on another line.\n  - name: @WORD@\n    options: &@NAME@ {ready: true, count: @N@}\ncopy: *@NAME@',
}
WORDS='amber birch coral drift ember flint grove hazel ivory jade laurel moss olive pebble quartz ridge spruce thistle umber vale'.split()
def main():
 root=PackSpec.open('yaml').dataset_root/'sources/curriculum-mixed-v1';files={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for v in range(24):
   word=WORDS[(index+v)%len(WORDS)];source=template.replace('@WORD@',word).replace('@NAME@',word+'_source').replace('@N@',str(random.Random(2424+index*67+v).randrange(2,80)))+'\n'
   if v%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();p=root/family/f'{v:02}.yaml';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve earlier mixed YAML task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original mixed YAML tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists() and p.read_bytes()!=license:raise ValueError('Preserve original mixed license')
 p.write_bytes(license);lock=dict(format='nsh-yaml-mixed-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve original mixed lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'mixed files in',len(TEMPLATES),'families')
if __name__=='__main__':main()
