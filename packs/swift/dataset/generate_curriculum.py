"""Original Swift task families, separate from Golden and displayed source."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash

TEMPLATES = {
'function': 'func @FN@(_ value: Int, by delta: Int = @N@) -> Int { value + delta }',
'labels': 'func @FN@(named name: String, count: Int) -> String { String(repeating: name, count: count) }',
'locals': 'func @FN@(_ values: [Int]) -> Int { var total = @N@; for value in values { total += value }; return total }',
'inout': 'func @FN@(_ value: inout Int, using action: (Int) -> Int) { value = action(value + @N@) }',
'variadic': 'func @FN@(_ values: Int...) -> Int { values.reduce(@N@, +) }',
'generic-function': 'func @FN@<T>(_ value: T, transform: (T) -> T) -> T { transform(value) }',
'generic-where': 'func @FN@<S: Sequence>(_ values: S) -> [S.Element] where S.Element: Hashable { Array(Set(values)) }',
'generic-box': 'struct @TYPE@<T> { var value: T; func map<U>(_ transform: (T) -> U) -> U { transform(value) } }',
'struct': 'struct @TYPE@ { let name: String; var count: Int = @N@; mutating func increment() { count += 1 } }',
'init': 'struct @TYPE@ { let value: Int; init(value: Int) { self.value = value + @N@ } }',
'failable-init': 'struct @TYPE@ { let name: String; init?(_ name: String) { guard !name.isEmpty else { return nil }; self.name = name } }',
'class': 'class @TYPE@ { var count = @N@; init(_ count: Int) { self.count = count }; func next() -> Int { count + 1 } }',
'inheritance': 'class Parent { func value() -> Int { @N@ } }; final class @TYPE@: Parent { override func value() -> Int { super.value() + 1 } }',
'deinit': 'final class @TYPE@ { let name: String; init(_ name: String) { self.name = name }; deinit { print(name) } }',
'enum': 'enum @TYPE@: String, CaseIterable { case ready = "@WORD@", waiting, finished }; func @FN@(_ value: @TYPE@) -> Bool { value == .ready }',
'associated-enum': 'enum @TYPE@<T> { case success(T), failure(String) }; func @FN@(_ value: @TYPE@<Int>) -> Int { switch value { case .success(let number): number; case .failure: @N@ } }',
'protocol': 'protocol @TYPE@ { associatedtype Item; var value: Item { get }; func update(_ value: Item) }',
'extension': 'struct @TYPE@ { let count: Int }; extension @TYPE@ { var doubled: Int { count * @N@ }; func label() -> String { "@WORD@" } }',
'protocol-extension': 'protocol @TYPE@ { var name: String { get } }; extension @TYPE@ { func @FN@() -> String { name.uppercased() } }',
'where-extension': 'extension Array where Element: Equatable { func @FN@(_ value: Element) -> Bool { contains(value) } }',
'get-set': 'struct @TYPE@ { private var storage = @N@; var value: Int { get { storage } set(next) { storage = next } } }',
'observers': 'struct @TYPE@ { var value: Int = @N@ { willSet(next) { print(next) } didSet(previous) { print(previous) } } }',
'static': 'struct @TYPE@ { static let shared = @TYPE@(); static func @FN@() -> Int { @N@ } }',
'subscript': 'struct @TYPE@ { var values: [Int]; subscript(index: Int) -> Int { get { values[index] } set { values[index] = newValue } } }',
'array': 'func @FN@(_ values: [Int]) -> [Int] { values.filter { $0 > @N@ }.map { $0 * 2 } }',
'dictionary': 'func @FN@(_ names: [String]) -> [String: Int] { Dictionary(uniqueKeysWithValues: names.map { ($0, $0.count + @N@) }) }',
'closure': 'func @FN@(_ values: [Int]) -> [Int] { values.map { value in value + @N@ } }',
'typed-closure': 'let @FN@: (Int) -> Int = { (number: Int) -> Int in number + @N@ }',
'capture': 'func @FN@(_ initial: Int) -> () -> Int { var count = initial; return { [step = @N@] in count += step; return count } }',
'weak-capture': 'final class @TYPE@ { var count = @N@; lazy var action: () -> Void = { [weak self] in self?.count += 1 } }',
'optional': 'func @FN@(_ input: String?) -> Int { if let text = input, let count = Int(text) { return count }; return @N@ }',
'guard': 'func @FN@(_ input: Int?) -> Int { guard let number = input else { return @N@ }; return number * 2 }',
'chaining': 'struct @TYPE@ { var name: String? }; func @FN@(_ item: @TYPE@?) -> Int { item?.name?.count ?? @N@ }',
'pattern': 'func @FN@(_ input: (Int, String)) -> String { let (number, label) = input; return number > @N@ ? label : "@WORD@" }',
'if-case': 'enum @TYPE@ { case item(Int), empty }; func @FN@(_ input: @TYPE@) -> Int { if case let .item(number) = input { return number }; return @N@ }',
'async': 'func @FN@(_ value: Int) async throws -> String { try await Task.sleep(for: .milliseconds(@N@)); return String(value) }',
'actor': 'actor @TYPE@ { private var count = @N@; func next() -> Int { count += 1; return count } }',
'async-let': 'func @FN@() async -> Int { async let left = Task { @N@ }.value; async let right = Task { 2 }.value; return await left + right }',
'async-stream': 'func @FN@(_ values: AsyncStream<Int>) async -> Int { var sum = @N@; for await value in values { sum += value }; return sum }',
'task-group': 'func @FN@(_ values: [Int]) async -> [Int] { await withTaskGroup(of: Int.self) { group in for value in values { group.addTask { value * @N@ } }; var result: [Int] = []; for await value in group { result.append(value) }; return result } }',
'main-actor': '@MainActor final class @TYPE@ { var count = @N@; func update() { count += 1 } }',
'error': 'enum @TYPE@: Error { case missing }; func @FN@(_ value: Int) throws -> Int { guard value > @N@ else { throw @TYPE@.missing }; return value }',
'catch': 'func @FN@(_ body: () throws -> Int) -> Int { do { return try body() } catch let problem { print(problem); return @N@ } }',
'typed-throws': 'enum @TYPE@: Error { case unavailable }; func @FN@() throws(@TYPE@) -> Int { throw .unavailable }',
'interpolation': 'func @FN@(_ name: String, count: Int) -> String { "@WORD@ \\(name): \\(count + @N@)" }',
'raw-string': 'let @FN@ = #"C:\\@WORD@\\file and \\(literal)"#',
'raw-interpolation': 'func @FN@(_ value: Int) -> String { #"@WORD@ \\#(value + @N@)"# }',
'multiline': 'func @FN@(_ title: String) -> String { """\n@WORD@\nTitle: \\(title)\nCount: @N@ 🌌\n""" }',
'regex': 'func @FN@(_ text: String) -> Bool { text.wholeMatch(of: /[a-z]+@[a-z]+\\.com/) != nil }',
'extended-regex': 'let @FN@ = #/[a-z]+ // @WORD@ [0-9]+/#',
'comments': '/// Original @WORD@ 🌌 documentation.\nfunc @FN@(_ value: Int) -> Int { /* outer /* nested */ tail */ value + @N@ } // end\n',
'property-wrapper': '@propertyWrapper struct @TYPE@<Value> { var wrappedValue: Value; init(wrappedValue: Value) { self.wrappedValue = wrappedValue } }; struct Storage { @@TYPE@ var value = @N@ }',
'attributes': '@available(macOS 14, iOS 17, *) @MainActor func @FN@() -> Int { @N@ }',
'result-builder': '@resultBuilder struct @TYPE@ { static func buildBlock(_ values: Int...) -> [Int] { values } }; @@TYPE@ func @FN@() -> [Int] { @N@; 2; 3 }',
'imports': 'import Foundation\nimport struct Foundation.URL\nfunc @FN@(_ text: String) -> URL? { URL(string: text) }',
'conditional': '#if DEBUG\nlet @FN@ = @N@\n#else\nlet @FN@ = 0\n#endif',
'typealias': 'typealias @TYPE@<T> = (T) -> String; func @FN@<T>(_ value: T, format: @TYPE@<T>) -> String { format(value) }',
'keypath': 'struct @TYPE@ { let name: String }; func @FN@(_ values: [@TYPE@]) -> [String] { values.map(\\.name) }',
'operator': 'struct @TYPE@ { let value: Int; static func + (left: Self, right: Self) -> Self { Self(value: left.value + right.value) } }',
'noncopyable': 'struct @TYPE@: ~Copyable { let value: Int; consuming func @FN@() -> Int { value + @N@ } }',
'opaque': 'func @FN@() -> some Sequence<Int> { [@N@, 2, 3] }; func use(_ values: any Sequence<Int>) { for value in values { print(value) } }',
'swiftui-view': 'import SwiftUI\nstruct @TYPE@: View { let title: String; var body: some View { VStack(alignment: .leading, spacing: @N@) { Text(title).font(.headline); Text("@WORD@") }.padding() } }',
'swiftui-state': 'import SwiftUI\nstruct @TYPE@: View { @State private var count = @N@; var body: some View { Button("Count: \\(count)") { count += 1 }.padding() } }',
'swiftui-binding': 'import SwiftUI\nstruct @TYPE@: View { @Binding var title: String; var body: some View { TextField("@WORD@", text: $title).padding(@N@) } }',
'swiftui-list': 'import SwiftUI\nstruct @TYPE@: View { let names: [String]; var body: some View { List(names, id: \\.self) { name in HStack { Image(systemName: "star"); Text(name) } } } }',
'swiftui-builder': 'import SwiftUI\nstruct @TYPE@: View { let ready: Bool; @ViewBuilder var body: some View { if ready { Text("@WORD@") } else { ProgressView() } } }',
'swiftui-preview': 'import SwiftUI\nstruct @TYPE@: View { var body: some View { Text("@WORD@").padding(@N@) } }; #Preview { @TYPE@() }',
'numbers': 'let @FN@: Double = 1_000 + 0xff + 0b1010 + 1.5e-3 + 0x1.fp2 + @N@',
}
WORDS = 'aurora bridge cosmos delta ember forest galaxy harbor island juniper kernel lumen meteor nova orbit prism quasar river solar tundra'.split()

def main():
    root = PackSpec.open('swift').dataset_root / 'sources/curriculum-v1'; files = {}
    for index,(family,template) in enumerate(TEMPLATES.items()):
        for variant in range(24):
            rng = random.Random(83017 + index*101 + variant); word = WORDS[(index+variant)%len(WORDS)]
            source = template.replace('@FN@',word+'Process').replace('@TYPE@',word.title()+'Value').replace('@N@',str(rng.randrange(2,30))).replace('@WORD@',word) + '\n'
            if variant%4 == 1: source = source.replace('\n','\r\n')
            raw = source.encode(); path = root / family / f'{variant:02}.swift'; path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists() and path.read_bytes() != raw: raise ValueError('Preserve previous Swift curriculum')
            if not path.exists(): path.write_bytes(raw)
            files[str(path.relative_to(root))] = hashlib.sha256(raw).hexdigest()
    license = b'Original Swift syntax tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or Playground copies.\n'
    path = root / 'LICENSE'
    if path.exists() and path.read_bytes() != license: raise ValueError('Preserve Swift curriculum license')
    path.write_bytes(license)
    lock = dict(format='nsh-swift-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest())
    path = root / 'source.lock.json'
    if path.exists() and json.loads(path.read_text()) != lock: raise ValueError('Preserve earlier Swift curriculum lock')
    path.write_text(json.dumps(lock,indent=2)+'\n')
    print(len(files),'original Swift tasks;',len(TEMPLATES),'families')

if __name__ == '__main__': main()
