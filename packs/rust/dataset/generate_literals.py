"""Original literal/context tasks from validation-only raw/format-string failures."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash

TEMPLATES={
'raw-return':'''fn render() -> &'static str { @RAW@ }''',
'raw-constant':'''const DOCUMENT: &str = @RAW@; fn main() { println!("{}", DOCUMENT); }''',
'raw-method':'''struct Message; impl Message { fn text(&self) -> &str { @RAW@ } }''',
'raw-closure':'''fn create() -> impl Fn() -> &'static str { || @RAW@ }''',
'raw-match':'''fn text(ready: bool) -> &'static str { match ready { true => @RAW@, false => "waiting" } }''',
'raw-replace':'''fn text() -> String { let value = @RAW@; value.replace("name", "title") }''',
'raw-bytes':'''fn length() -> usize { let request = @BYTE@; request.len() }''',
'raw-byte-array':'''const REQUESTS: [&[u8]; 2] = [@BYTE@, b"plain"]; fn count() -> usize { REQUESTS.len() }''',
'c-strings':'''fn c_text() -> &'static std::ffi::CStr { @CSTR@ }''',
'string-tuple':'''fn text() -> (String, usize) { let value = @RAW@; (value.to_owned(), value.len()) }''',
'format-fields':'''fn show(name: &str, count: usize) -> String { format!("{name}: {count} 🌌") }''',
'format-width':'''fn show(value: f64, width: usize) -> String { format!("value={value:>width$.3} (🌿)") }''',
'format-debug':'''fn show(items: &[u32]) { println!("Items: {items:#?}; length={}", items.len()); }''',
'format-macro':'''macro_rules! log_value { ($name:expr, $value:expr) => { println!("{}: {:?}", $name, $value) }; } fn main() { log_value!("🌌", @RAW@); }''',
'raw-iter':'''fn words() -> Vec<String> { let text = @RAW@; text.lines().map(|line| line.to_owned()).collect() }''',
'nested-comment':'''/* outer block /* nested "string" */ still comment */ fn show() { let text = @RAW@; println!("Text: {text}; {{escaped}}"); }''',
}
TEXTS=['{ "name": "Aurora", "path": "C:\\data" }','<section class="card">{value} &amp; end</section>','SELECT "title" FROM "items" WHERE id = 42;','fn main() { println!("not code"); }','(?P<name>[A-Za-z_]+)\\s*=\\s*".*?"','line one\nline two with "quotes"\nend']
def main():
 root=PackSpec.open('rust').dataset_root/'sources/literals-v1';files={}
 for family,template in TEMPLATES.items():
  for i in range(32):
   hashes='#'*(1+i%4);text=TEXTS[i%len(TEXTS)];raw='r'+hashes+'"'+text+'"'+hashes;byte='br'+hashes+'"'+text+'"'+hashes;cstr='cr'+hashes+'"'+text+'"'+hashes
   source=template.replace('@RAW@',raw).replace('@BYTE@',byte).replace('@CSTR@',cstr)+'\n'
   if i%5==0:source=source.replace('\n','\r\n')
   if i%7==0:source='// Original literal context 🌌\n'+source
   data=source.encode();path=root/family/f'{i:02}.rs';path.parent.mkdir(parents=True,exist_ok=True)
   if path.exists() and path.read_bytes()!=data:raise ValueError('Preserve prior Rust literal curriculum')
   if not path.exists():path.write_bytes(data)
   files[str(path.relative_to(root))]=hashlib.sha256(data).hexdigest()
 path=root/'LICENSE'
 if not path.exists():path.write_text('Original Rust literal/context tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or Playground copies.\n')
 lock=dict(format='nsh-rust-literals-v1',generatorSha256=file_hash(Path(__file__)),files=files);path=root/'source.lock.json'
 if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Preserve prior literal lock')
 path.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'literal/context tasks')
if __name__=='__main__':main()
