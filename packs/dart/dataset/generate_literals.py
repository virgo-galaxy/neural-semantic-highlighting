"""Bounded original literal/context revision, retaining the initial task corpus."""
from pathlib import Path
import json,hashlib
from training.shared.spec import PackSpec,file_hash

TEMPLATES={
'raw-regex-context':r"""class @TYPE@ { bool valid(String name) { final rule = RegExp(r'^[a-z][a-z0-9_]*$'); return rule.hasMatch(name); } String path() => r'C:\@WORD@\docs'; }""",
'raw-document-context':"""const @FN@ = r'''{
  "title": "@WORD@",
  "path": "C:\\data",
  "template": "$literal // not a comment"
}''';
String render() => @FN@;
""",
'triple-interpolation':"""String @FN@(String name, int count) => '''@WORD@
Hello, $name!
There are $count records 🌌.
Total: ${count + 1}
''';""",
'mixed-function-context':"""class @TYPE@ { final String name; @TYPE@(this.name); String get title => 'Hello, $name!'; }
String @FN@(String value) { final item = @TYPE@(value); return '${item.title}: @WORD@'; }
void main() { final name = '@WORD@'; print(@FN@(name)); }
""",
'multi-interpolation':"""String @FN@(String name, int count) => '$name has $count @WORD@ entries.';
String combine(List<String> values) => '${values.length} -> ${values.map((item) => item.trim()).join(", ")}';
""",
'literal-methods':r"""class @TYPE@ { String quote(String name) => "A \"$name\" @WORD@"; String raw() => r'\n ${literal}'; String pattern() => r'^\w+\s+[a-z]+$'; }""",
'closure-context':"""List<String> @FN@(List<String> names) { String clean(String value) => value.trim(); final decorate = (name) => '$name @WORD@'; return names.map((name) => decorate(clean(name))).toList(); }""",
'typed-callback-context':"""String @FN@(String apply(String text), String value) { final convert = (String item) => apply(item); return '@WORD@: ${convert(value)}'; }""",
}
def main():
    root=PackSpec.open('dart').dataset_root/'sources/literals-v1';files={}
    for family,template in TEMPLATES.items():
        for i in range(24):
            word=['aurora','comet','galaxy','harbor','island','juniper'][i%6]+str(i)
            source=template.replace('@TYPE@',word.title()+'Item').replace('@FN@',word+'Render').replace('@WORD@',word)+'\n'
            if i%4==1:source=source.replace('\n','\r\n')
            raw=source.encode();p=root/family/f'{i:02}.dart';p.parent.mkdir(parents=True,exist_ok=True)
            if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve earlier Dart literal revision')
            if not p.exists():p.write_bytes(raw)
            files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
    p=root/'LICENSE'
    if not p.exists():p.write_text('Original Dart literal/context tasks for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or Playground copies.\n')
    lock=dict(format='nsh-dart-literals-v1',generatorSha256=file_hash(Path(__file__)),files=files);p=root/'source.lock.json'
    if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve original literal revision lock')
    p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'bounded literal/context tasks')
if __name__=='__main__':main()
