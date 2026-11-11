"""Original mixed literal/closure families added after initial validation review."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash

TEMPLATES = {
'shorthand-chain': 'func @FN@(_ items: [Int]) -> [Int] { items.filter { $0 > @N@ }.sorted { $0 < $1 }.map { $0 + @N@ } }',
'numbered-closure': 'func @FN@(_ values: [String: Int]) -> [String] { values.sorted { $0.key < $1.key }.map { "\\($0.key)=\\($0.value + @N@) @WORD@" } }',
'projected-binding': 'import SwiftUI\nstruct @TYPE@: View { @Binding var name: String; @State var enabled = true; var body: some View { VStack { TextField("@WORD@", text: $name); Toggle("Enabled", isOn: $enabled) }.padding(@N@) } }',
'keyword-label': 'func @FN@(for owner: String, from value: Int, with suffix: String = "@WORD@") -> String { "\\(owner): \\(value + @N@) \\(suffix)" }',
'enum-labels': 'enum @TYPE@ { case idle, entry(label: String, count: Int) }; func @FN@(_ item: @TYPE@) -> String { switch item { case .idle: "@WORD@"; case .entry(let label, let count): "\\(label): \\(count + @N@)" } }',
'raw-mixed': 'func @FN@(_ value: Int) -> String { let raw = #"C:\\@WORD@\\data \\(ordinary) // literal"#; let rx = #/[a-z]+\\.[0-9]+/#; return "\\(raw) \\(value + @N@) \\(rx)" }',
'double-pound': 'func @FN@(_ value: Int) -> String { let text = ##"@WORD@ \\##(value + @N@) and \\(ordinary) and "quotes""##; return text }',
'continued': 'func @FN@(_ name: String) -> String { """\nHello \\(name) @WORD@ \\\ncontinued \\(@N@ + 1) 🌌\n""" }',
'long-continued': 'func @FN@(_ count: Int) -> String { """\n@LONG@\n\\(count + @N@) @WORD@ \\\nend of message\n""" }',
'escapes': r'func @FN@(_ text: String) -> String { "@WORD@ \"quoted\" \\ path\nNext: \(text), total: \(@N@)" }',
'associated-type': 'protocol @TYPE@ { associatedtype Value; var value: Value { get } }; func @FN@<T: @TYPE@>(_ item: T, transform: (T.Value) -> String) -> String { transform(item.value) }',
'closure-signature': 'func @FN@(_ values: [Int]) -> [Int] { values.map { (number: Int) -> Int in number + @N@ }.map { count in count * 2 } }',
}
WORDS='alpine beacon canyon drizzle eclipse feather glimmer horizon iceberg jasmine kingdom lantern meadow nebula oasis pebble quartz ripple summit timber'.split()

def main():
 root=PackSpec.open('swift').dataset_root/'sources/literals-v1';files={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   rng=random.Random(62419+index*101+variant);word=WORDS[(index+variant)%len(WORDS)]
   source=template.replace('@FN@',word+'Compose').replace('@TYPE@',word.title()+'Entry').replace('@N@',str(rng.randrange(3,40))).replace('@WORD@',word).replace('@LONG@',(word+' preserve original text ') * (15+variant%9))+'\n'
   if variant%4==1: source=source.replace('\n','\r\n')
   path=root/family/f'{variant:02}.swift';raw=source.encode();path.parent.mkdir(parents=True,exist_ok=True)
   if path.exists() and path.read_bytes()!=raw: raise ValueError('Preserve previous Swift mixed tasks')
   if not path.exists(): path.write_bytes(raw)
   files[str(path.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original mixed Swift literal and closure tasks authored for Neural Semantic Highlighting.\nNo upstream, Golden or displayed-source copies.\n'
 path=root/'LICENSE'
 if path.exists() and path.read_bytes()!=license: raise ValueError('Preserve original task license')
 path.write_bytes(license)
 lock=dict(format='nsh-swift-literals-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest())
 path=root/'source.lock.json'
 if path.exists() and json.loads(path.read_text())!=lock: raise ValueError('Preserve previous mixed-task lock')
 path.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'mixed Swift tasks;',len(TEMPLATES),'families')

if __name__=='__main__': main()
