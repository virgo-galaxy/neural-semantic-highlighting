"""Original Rust syntax tasks. All variants keep their task family."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash

TEMPLATES={
'function':'''pub fn @FN@(value: i32, extra: i32) -> i32 { value * @N@ + extra }''',
'mutable':'''fn @FN@(limit: usize) -> usize { let mut total = @N@; for i in 0..limit { total += i; } total }''',
'borrow':'''fn @FN@<'a>(left: &'a str, right: &'a str) -> &'a str { if left.len() > right.len() { left } else { right } }''',
'borrow-array':'''fn @FN@<'a, T>(values: &'a [T]) -> Option<&'a T> { values.first() }''',
'borrow-struct':'''struct @TYPE@<'a> { name: &'a str, size: usize } impl<'a> @TYPE@<'a> { fn @FN@(&self) -> &'a str { self.name } }''',
'struct':'''#[derive(Debug, Clone)] struct @TYPE@ { name: String, count: u32 } impl @TYPE@ { fn @FN@(name: String) -> Self { Self { name, count: @N@ } } fn count(&self) -> u32 { self.count } }''',
'field-update':'''struct @TYPE@ { x: f64, y: f64 } fn @FN@(point: @TYPE@) -> @TYPE@ { @TYPE@ { x: point.x + @N@.0, ..point } }''',
'unit-tuple':'''struct @TYPE@(u64); struct Marker; fn @FN@(value: @TYPE@) -> u64 { value.0 + @N@ }''',
'enum':'''enum @TYPE@ { Idle, Active(u32), Failed { message: String } } fn @FN@(state: @TYPE@) -> u32 { match state { @TYPE@::Idle => 0, @TYPE@::Active(value) => value, @TYPE@::Failed { message } => message.len() as u32 } }''',
'enum-discriminant':'''#[repr(u8)] enum @TYPE@ { Low = @N@, High = 100 } fn @FN@() -> u8 { @TYPE@::High as u8 }''',
'trait':'''trait @TYPE@ { fn value(&self) -> usize; } struct Item(usize); impl @TYPE@ for Item { fn value(&self) -> usize { self.0 } } fn @FN@(item: &dyn @TYPE@) -> usize { item.value() }''',
'trait-associated':'''trait @TYPE@ { type Item; fn @FN@(&mut self) -> Option<Self::Item>; }''',
'generic-bound':'''fn @FN@<T: Clone + Default>(items: &[T]) -> Vec<T> { items.iter().cloned().collect() }''',
'where':'''fn @FN@<T, F>(value: T, transform: F) -> String where T: Clone, F: FnOnce(T) -> String { transform(value.clone()) }''',
'const-generic':'''struct @TYPE@<T, const N: usize> { values: [T; N] } impl<T, const N: usize> @TYPE@<T, N> { fn @FN@(&self) -> usize { N } }''',
'alias':'''type @TYPE@<T> = Result<T, String>; fn @FN@(text: &str) -> @TYPE@<u32> { text.parse().map_err(|error| format!("{}", error)) }''',
'option-let':'''fn @FN@(value: Option<u32>) -> u32 { if let Some(found) = value { found + @N@ } else { 0 } }''',
'let-else':'''fn @FN@(input: Option<&str>) -> usize { let Some(text) = input else { return 0; }; text.len() }''',
'match-guards':'''fn @FN@(value: i32) -> &'static str { match value { n if n < 0 => "negative", 0 => "zero", 1..=9 => "small", _ => "large" } }''',
'destructure':'''fn @FN@(pair: (i32, i32)) -> i32 { let (left, right) = pair; let [first, ..] = [left, right]; first + right }''',
'struct-pattern':'''struct @TYPE@ { name: String, count: u32 } fn @FN@(item: @TYPE@) -> u32 { let @TYPE@ { name: title, count } = item; count + title.len() as u32 }''',
'for-pattern':'''fn @FN@(items: &[(u32, u32)]) -> u32 { let mut sum = 0; for (left, right) in items { sum += left + right; } sum }''',
'while-let':'''fn @FN@(mut values: Vec<u8>) -> usize { let mut count = @N@; while let Some(value) = values.pop() { count += value as usize; } count }''',
'loop-label':'''fn @FN@(limit: usize) -> usize { let mut value = 0; 'outer: loop { for i in 0..limit { if i > @N@ { break 'outer; } value += i; } break; } value }''',
'closure':'''fn @FN@(items: &[i32]) -> Vec<i32> { let bias = @N@; let transform = |value: &i32| value + bias; items.iter().map(transform).collect() }''',
'move-closure':'''fn @FN@(name: String) -> impl FnOnce() -> String { move || format!("@WORD@: {}", name) }''',
'async':'''async fn @FN@(value: u32) -> u32 { async { value + @N@ }.await }''',
'async-result':'''async fn @FN@() -> Result<String, std::io::Error> { let value = fetch().await?; Ok(value) }''',
'async-move':'''fn @FN@(name: String) -> impl std::future::Future<Output = String> { async move { name } }''',
'modules':'''pub mod @FN@ { pub const LIMIT: usize = @N@; pub fn compute(value: usize) -> usize { value + LIMIT } } use @FN@::compute; fn run() -> usize { compute(2) }''',
'use-tree':'''use std::{fmt::Debug, collections::HashMap}; use std::io::Result as IoResult; pub fn @FN@(items: HashMap<String, usize>) -> usize { items.len() }''',
'constants':'''const LIMIT: usize = @N@; static NAME: &str = "@WORD@"; fn @FN@(value: usize) -> bool { value < LIMIT && !NAME.is_empty() }''',
'macro-call':'''fn @FN@(value: i32) { println!("@WORD@: {}", value); let values = vec![@N@, value]; assert_eq!(values.len(), 2); }''',
'macro-rule':'''macro_rules! @FN@ { ($value:expr) => { $value * @N@ }; } fn run() -> i32 { @FN@!(3) }''',
'macro-repeat':'''macro_rules! @FN@ { ($($item:expr),* $(,)?) => { vec![$($item),*] }; } fn run() { let items = @FN@!(1, @N@, 3); }''',
'attribute':'''#[derive(Debug, Default)] struct @TYPE@ { value: usize } #[inline] #[must_use] fn @FN@() -> @TYPE@ { @TYPE@ { value: @N@ } }''',
'cfg-attribute':'''#[cfg(feature = "@WORD@")] pub fn @FN@() { println!("ready"); } #[cfg(not(feature = "@WORD@"))] pub fn fallback() {}''',
'unsafe-extern':'''unsafe extern "C" { fn external(value: i32) -> i32; } unsafe fn @FN@(pointer: *const i32) -> i32 { unsafe { *pointer } }''',
'unsafe-attribute':'''#[unsafe(no_mangle)] pub extern "C" fn @FN@(value: u32) -> u32 { value + @N@ }''',
'raw-strings':'''fn @FN@() { let json = r##"{ "name": "@WORD@", "path": "C:\\temp" }"##; let bytes = br#"GET / HTTP/1.1"#; let cstr = c"ready"; println!("{} {:?}", json, bytes); }''',
'chars':'''fn @FN@() -> char { let text = "@WORD@ 🌌"; let byte = b'X'; let escaped = '\\n'; '星' }''',
'numeric':'''fn @FN@() { let hex = 0xff_u32; let binary = 0b1010u8; let decimal = 1_000usize; let float = 1.25e-3_f64; let negative = -@N@i32; }''',
'comments':'''//! @WORD@ module documentation
/// Compute a value with original Unicode 🌌.
fn @FN@(value: i32) -> i32 { /* outer /* nested */ comment */ value + @N@ }''',
'raw-identifiers':'''fn r#type(r#match: usize) -> usize { let r#gen = r#match + @N@; r#gen }''',
'iterator':'fn @FN@(values: &[u32]) -> Vec<u32> { values.iter().copied().filter(|v| *v > @N@).map(|v| v * 2).collect() }',
'question-mark':'fn @FN@(text: &str) -> Result<u32, std::num::ParseIntError> { let value: u32 = text.parse()?; Ok(value + @N@) }',
'let-chain':'fn @FN@(value: Option<u32>) -> bool { if let Some(n) = value && n > @N@ { true } else { false } }',
'higher-ranked':'''fn @FN@<F>(visit: F) where F: for<'a> Fn(&'a str) -> &'a str { let text = visit("@WORD@"); println!("{}", text); }''',
}
WORDS='aurora bridge cosmos delta ember forest galaxy harbor island juniper kernel lumen meteor nova orbit prism quasar river solar tundra'.split()
def main():
 root=PackSpec.open('rust').dataset_root/'sources/curriculum-v1';files={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   rng=random.Random(91700+index*101+variant);word=WORDS[(index+variant)%len(WORDS)];source=template.replace('@FN@',word+'_process').replace('@TYPE@',word.title()+'Value').replace('@N@',str(rng.randrange(2,30))).replace('@WORD@',word)+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();path=root/family/f'{variant:02}.rs';path.parent.mkdir(parents=True,exist_ok=True)
   if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve previous Rust curriculum')
   if not path.exists():path.write_bytes(raw)
   files[str(path.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 path=root/'LICENSE'
 if not path.exists():path.write_text('Original Rust syntax tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or Playground copies.\n')
 lock=dict(format='nsh-rust-curriculum-v1',generatorSha256=file_hash(Path(__file__)),files=files);path=root/'source.lock.json'
 if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Preserve previous curriculum lock')
 path.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'original Rust tasks in',len(TEMPLATES),'families')
if __name__=='__main__':main()
