"""Original YAML configuration families, separate from Golden and display examples."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
TEMPLATES={
'mapping':'name: @WORD@\nenabled: true\nport: @N@\nowner: null',
'sequence':'records:\n  - name: @WORD@\n    weight: @N@\n  - name: extra\n    weight: 2\nactive: false',
'flow':'options: {name: @WORD@, retries: @N@, ready: true}\nlabels: [api, docs, null]\npaths: {root: ./@WORD@, cache: ./cache}',
'workflow':'name: @WORD@ pipeline\non: [push, pull_request]\njobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: echo "@WORD@"\n        timeout-minutes: @N@',
'workflow-expressions':'name: @WORD@ checks\non:\n  push:\n    branches: [main]\njobs:\n  lint:\n    if: ${{ github.ref != \'refs/heads/archive\' }}\n    env:\n      PROJECT: ${{ github.repository }}\n    steps:\n      - run: echo "${PROJECT}"\n        timeout-minutes: @N@',
'workflow-matrix':'jobs:\n  @WORD@:\n    strategy:\n      fail-fast: false\n      matrix:\n        node: [20, 22, @N@]\n        os: [ubuntu-latest, macos-latest]\n    runs-on: ${{ matrix.os }}\n    steps:\n      - uses: actions/setup-node@v4',
'compose':'services:\n  @WORD@:\n    image: example/@WORD@:latest\n    ports: ["@N@:8080"]\n    environment:\n      LOG_LEVEL: info\n      FEATURE: "true"\n    restart: unless-stopped\nvolumes:\n  data: {}',
'compose-health':'services:\n  worker:\n    image: @WORD@/worker\n    healthcheck:\n      test: [CMD, curl, -f, http://localhost:8080]\n      interval: 10s\n      retries: @N@\n    labels:\n      app.name: @WORD@\nnetworks: {internal: {driver: bridge}}',
'kubernetes':'apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: @WORD@\nspec:\n  replicas: @N@\n  selector:\n    matchLabels: {app: @WORD@}\n  template:\n    metadata:\n      labels: {app: @WORD@}\n    spec:\n      containers:\n        - name: web\n          image: example/@WORD@:1.0',
'kubernetes-service':'apiVersion: v1\nkind: Service\nmetadata: {name: @WORD@}\nspec:\n  selector: {app: @WORD@}\n  ports:\n    - port: @N@\n      targetPort: 8080\n      protocol: TCP\n  type: ClusterIP',
'prometheus':'global:\n  scrape_interval: 15s\n  evaluation_interval: 30s\nscrape_configs:\n  - job_name: @WORD@\n    static_configs:\n      - targets: ["localhost:@N@"]\n        labels: {region: east, tier: api}',
'alert-rules':'groups:\n  - name: @WORD@\n    rules:\n      - alert: HighLatency\n        expr: request_seconds > @N@\n        for: 5m\n        labels: {severity: warning}\n        annotations:\n          summary: "Latency for {{ $labels.instance }}"',
'helm-values':'replicaCount: @N@\nimage:\n  repository: example/@WORD@\n  tag: latest\n  pullPolicy: IfNotPresent\nresources:\n  limits: {cpu: 500m, memory: 256Mi}\ningress: {enabled: false, hosts: []}',
'gitlab':'stages: [lint, build]\n@WORD@:\n  stage: build\n  image: node:22\n  script:\n    - npm ci\n    - npm run build\n  retry: @N@\n  rules:\n    - if: \'$CI_COMMIT_BRANCH == "main"\'',
'cloud-tags':'Resources:\n  @WORD@:\n    Type: AWS::S3::Bucket\n    Properties:\n      BucketName: !Sub "${Project}-@WORD@"\nOutputs:\n  Name:\n    Value: !Ref @WORD@\n  Endpoint:\n    Value: !GetAtt [@WORD@, Arn]',
'anchor-map':'defaults: &@NAME@\n  retries: @N@\n  active: true\ncopy: *@NAME@\nlabel: @WORD@',
'anchor-sequence':'targets: &@NAME@ [@WORD@, local, remote]\nregions:\n  east: *@NAME@\n  west: [other, backup]\nlimit: @N@',
'merge-anchor':'base: &@NAME@ {image: example/@WORD@, replicas: @N@}\nproduction:\n  <<: *@NAME@\n  debug: false\n  tags: [release, stable]',
'anchor-nested':'templates:\n  primary: &@NAME@\n    name: @WORD@\n    ports: [@N@, 8080]\n    enabled: true\ninstances:\n  - config: *@NAME@\n    region: north',
'anchor-block':'script: &@NAME@ |-\n  echo "@WORD@"\n  # keep this literal\n  printf "%s" "$HOME"\nsteps:\n  - run: *@NAME@\n    retries: @N@',
'anchor-tags':'root: &@NAME@ !Settings\n  name: @WORD@\n  retries: @N@\n  features: [true, false]\ncopy: *@NAME@\nkind: !<tag:example.test,2026:kind> worker',
'literal-run':'steps:\n  - name: @WORD@\n    run: |\n      echo "${WORKSPACE}"\n      # shell-looking content stays a string\n      count=@N@\n      printf "%s\\n" "$count"\n    enabled: true',
'folded-description':'metadata:\n  title: @WORD@\n  description: >-\n    A configuration for @WORD@ with several words\n    and a second original source line.\n  tags: [docs, sample]\nrevision: @N@',
'chomp-keep':'message: |+\n  @WORD@ with trailing blank lines\n\n\nlimit: @N@\nflags: {ready: true, cached: false}',
'indent-chomp':'config:\n  content: |2- # raw @WORD@ content\n    key: value\n    # not a YAML comment here\n    [one, two, @N@]\n  mode: literal\nactive: true',
'block-markup':'page: |-\n  <section class="@WORD@">\n    <h1>${title} is text</h1>\n    <!-- YAML: not parsed -->\n  </section>\noptions: {count: @N@, enabled: false}',
'block-json':'payload: >\n  { "name": "@WORD@",\n    "value": @N@, "active": true }\ncontentType: application/json\nheaders: [accept, source]',
'block-comment-header':'message: >2+ # @WORD@ description\n  Keep "quotes", ${expressions} and # markers literal.\n  Preserve source rather than applying semantic folding.\n\nsummary: @WORD@\ncount: @N@',
'multi-document':'---\nkind: ConfigMap\nmetadata: {name: @WORD@}\ndata: {mode: test, count: "@N@"}\n...\n---\nkind: Service\nmetadata: {name: @WORD@-api}\nspec: {ports: [@N@, 8080]}',
'directives':'%YAML 1.2\n---\napplication: @WORD@\ncount: @N@\nready: true\n...\n',
'tag-directive':'%TAG !cfg! tag:example.test,2026:\n---\nconfig: !cfg!settings\n  title: @WORD@\n  threshold: @N@\n  options: [yes, no, on, off]',
'explicit-keys':'? [@WORD@, primary]\n: {weight: @N@, ready: true}\n? secondary\n: [one, two, null]',
'quoted-keys':'"@WORD@.name": "Project @WORD@"\n\'path:root\': \'C:\\projects\\@WORD@\'\n"# label": "# literal"\ncounts: [@N@, 0]',
'escaped-strings':'name: @WORD@\ntext: "Quoted \\"value\\", slash \\\\ and newline\\n"\npath: \'C:\\workspace\\@WORD@\'\ncount: @N@\nflags: [true, null]',
'opaque-expressions':'command: "node -e \\"console.log(1)\\""\nexpression: ${{ matrix.@WORD@ }}\npattern: \'^\\w+\\d+$\'\nurl: https://example.test/@WORD@#section\noptions: {limit: @N@, ready: true}',
'plain-multiline':'description: A @WORD@ message\n  that continues on the next line\n  without becoming a collection.\nsettings: {limit: @N@, enabled: true}\nnames: [alpha, beta]',
'quoted-multiline':'message: "A @WORD@ message\n  spanning original source lines\n  with an escaped \\"quote\\"."\nrecords:\n  - count: @N@\n    label: raw',
'core-literals':'values: [true, false, null, ~, @N@, -1.25e+2, 0xff, 0o17, .inf, .nan]\nstrings: [yes, no, on, off, 1_000, 2026-11-11]\nname: @WORD@',
'null-empty':'title: @WORD@\nempty: # implicit null\nquoted: ""\nnullValue: null\nitems: []\nobject: {}\ncount: @N@',
'unicode':'标题🌌: @WORD@\nmessage: "星空 👩🏽‍💻 café é"\nrows:\n  - 名称: @WORD@\n    数量: @N@\nactive: true',
'comments':'# @WORD@ service 🌌\nname: @WORD@ # inline note\n# Keep the following numeric token.\nlimits:\n  retries: @N@\n  enabled: true\nstrings: ["# data", \'not # a comment\']',
'dates-strings':'release: 2026-11-11\nclock: 12:34:56\nbuild: @N@\nproject: @WORD@\nquoted: ["true", "null", "123"]',
'long-block':'article:\n  name: @WORD@\n  body: |-\n'+''.join('    @WORD@ source text with "quotes", # characters, {braces} and 🌌.\n' for _ in range(14))+'  draft: true\nversions: [@N@, 2]',
'long-plain':'name: @WORD@\nsummary: '+('The @WORD@ source contains a long plain scalar with 🌌 data. '*24)+'\nsettings: {limit: @N@, ready: true}',
'long-quoted':'metadata:\n  name: @WORD@\n  content: "'+('Original @WORD@ data with \\"quotes\\" and # literal text. '*18)+'"\n  count: @N@\nlabels: [preview, full]',
}
WORDS='aspen brook cypress delta elm forest glade heath island juniper kelp lotus mist north ocean pine quartz reed sage thyme'.split()
def main():
 root=PackSpec.open('yaml').dataset_root/'sources/curriculum-v1';files={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   word=WORDS[(index+variant)%len(WORDS)];source=template.replace('@WORD@',word).replace('@NAME@',word+'_base').replace('@N@',str(random.Random(1212+index*101+variant).randrange(3,90)))+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   if variant%11==3:source='\ufeff'+source
   raw=source.encode();p=root/family/f'{variant:02}.yaml';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve previous YAML task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original YAML tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists() and p.read_bytes()!=license:raise ValueError('Preserve original YAML license')
 p.write_bytes(license);lock=dict(format='nsh-yaml-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve original YAML lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'files in',len(TEMPLATES),'families')
if __name__=='__main__':main()
