"""Original Dart tasks, separate from Golden/Playground and grouped before windows."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash

TEMPLATES={
'functions':'''int @FN@(int value, {int count = @N@}) { final total = value + count; return total; }''',
'arrow':'''String @FN@(String value, [String suffix = "@WORD@"]) => value.trim() + suffix;''',
'closure':'''List<int> @FN@(List<int> values) { final bias = @N@; return values.where((v) => v > bias).map((v) => v * 2).toList(); }''',
'callback':'''T @FN@<T>(T value, T Function(T input) action) { return action(value); }''',
'class':'''class @TYPE@ { final String name; int count; @TYPE@(this.name, {this.count = @N@}); String label() => '$name: $count'; }''',
'constructor':'''class @TYPE@ { final int value; const @TYPE@(this.value); const @TYPE@.zero() : value = 0; @TYPE@ scale(int count) => @TYPE@(value * count); }''',
'factory':'''class @TYPE@ { final String name; @TYPE@._(this.name); factory @TYPE@.parse(String text) { return @TYPE@._(text.trim()); } }''',
'redirect':'''abstract class @TYPE@ { factory @TYPE@(int value) = Item; int get value; } class Item implements @TYPE@ { final int value; Item(this.value); }''',
'get-set':'''class @TYPE@ { int _count = @N@; int get count => _count; set count(int value) { _count = value.clamp(0, 100); } }''',
'cascade':'''class @TYPE@ { int count = 0; void add(int value) { count += value; } } void @FN@() { final item = @TYPE@()..count = @N@..add(2); print(item.count); }''',
'generics':'''class @TYPE@<T extends Object> { final List<T> values; @TYPE@(this.values); T get first => values.first; void add(T value) => values.add(value); }''',
'generic-function':'''Map<K, V> @FN@<K, V>(Iterable<K> keys, V Function(K key) build) => {for (final key in keys) key: build(key)};''',
'typedef':'''typedef @TYPE@<T> = T Function(T value, {required String name}); T @FN@<T>(@TYPE@<T> action, T value) => action(value, name: '@WORD@');''',
'enum':'''enum @TYPE@ { pending, active, complete } bool @FN@(@TYPE@ value) => value == @TYPE@.active;''',
'enhanced-enum':'''enum @TYPE@ { small(1), large(@N@); final int value; const @TYPE@(this.value); bool get ready => value > 1; }''',
'mixin':'''mixin @TYPE@ { String get name; String describe() => 'Hello $name'; } class Item with @TYPE@ { final String name; Item(this.name); }''',
'extension':'''extension @TYPE@ on String { bool get ready => trim().isNotEmpty; String @FN@() => '$this @WORD@'; }''',
'extension-type':'''extension type @TYPE@(int value) { bool get positive => value > 0; @TYPE@ next() => @TYPE@(value + @N@); }''',
'sealed':'''sealed class @TYPE@ {} final class Success extends @TYPE@ { final int value; Success(this.value); } final class Failure extends @TYPE@ {} String @FN@(@TYPE@ result) => switch(result) { Success(:final value) => '$value', Failure() => '@WORD@' };''',
'modifiers':'''abstract interface class @TYPE@ { int get value; } base class Item implements @TYPE@ { @override final int value; Item(this.value); } final class Child extends Item { Child(super.value); }''',
'record':'''(String, int) @FN@(String text) { return (text.trim(), @N@); } void run() { final (name, count) = @FN@('@WORD@'); print('$name $count'); }''',
'named-record':'''({String name, int count}) @FN@() => (name: '@WORD@', count: @N@); void run() { final (:name, :count) = @FN@(); print(name); print(count); }''',
'list-pattern':'''int @FN@(Object value) { if (value case [int head, ...final tail]) { return head + tail.length; } return @N@; }''',
'map-pattern':'''String @FN@(Map<String, Object?> value) => switch(value) { {'name': String name, 'count': int count} when count > @N@ => name, _ => '@WORD@' };''',
'object-pattern':'''class @TYPE@ { final int x, y; @TYPE@(this.x, this.y); } int @FN@(Object value) { if (value case @TYPE@(:var x, y: final height)) { return x + height; } return @N@; }''',
'pattern-assignment':'''void @FN@() { var left = @N@; var right = 2; (left, right) = (right, left); print(left); }''',
'for-pattern':'''int @FN@(List<(int, int)> values) { var sum = @N@; for (final (left, right) in values) { sum += left + right; } return sum; }''',
'async':'''Future<String> @FN@(Future<String> value) async { final text = await value; return text.trim() + '@WORD@'; }''',
'async-stream':'''Stream<int> @FN@(Stream<int> values) async* { await for (final value in values) { if (value > @N@) yield value; } }''',
'sync-generator':'''Iterable<int> @FN@(int count) sync* { for (var index = 0; index < count; index++) { yield index + @N@; } }''',
'future-list':'''Future<List<String>> @FN@(List<Future<String>> values) async { final result = await Future.wait(values); return [for (final item in result) item.trim()]; }''',
'interpolation':'''String @FN@(String name, int count) => "@WORD@ $name: ${count + @N@}";''',
'interpolation-member':'''String @FN@(List<String> values) => '${values.length} items: ${values.map((s) => s.trim()).join(", ")} @WORD@';''',
'raw-string':'''String @FN@() { final path = r'C:\\@WORD@\\data'; final pattern = RegExp(r'^[a-z]+$'); return '$path ${pattern.pattern}'; }''',
'multiline':'''String @FN@(String name) => """@WORD@\nHello $name 🌌\nTotal: ${@N@ + 1}\n""";''',
'raw-multiline':"""const @FN@ = r'''@WORD@\n{ "path": "C:\\data", "literal": "$name" }\n''';""",
'strings-escape':r"""String @FN@() => 'quoted \'@WORD@\' and \\ and \n';""",
'collections':'''Map<String, List<int>> @FN@(List<int> values) => {'@WORD@': [@N@, ...values, if (values.isEmpty) 0, for (final x in values) x * 2]};''',
'nullable-collections':'''List<int> @FN@(List<int>? values, int? first) => [?first, ...?values, @N@];''',
'null-safety':'''String @FN@(String? value) { final name = value?.trim() ?? '@WORD@'; String? result; result ??= name; return result!; }''',
'late-final':'''class @TYPE@ { final String name; late final int count = name.length + @N@; @TYPE@(this.name); }''',
'exception':'''int @FN@(String text) { try { return int.parse(text); } on FormatException catch (error, stack) { print('$error $stack'); return @N@; } finally { print('@WORD@'); } }''',
'imports':'''import 'dart:convert' as codec show jsonEncode; export 'dart:async' show Future; String @FN@(Object value) => codec.jsonEncode(value);''',
'annotation':'''@Deprecated('use @WORD@') class @TYPE@ { @override String toString() => '@WORD@'; }''',
'operator':'''class @TYPE@ { final int value; const @TYPE@(this.value); @TYPE@ operator +(@TYPE@ other) => @TYPE@(value + other.value); int operator [](int index) => value + index; }''',
'label':'''int @FN@(int limit) { var result = @N@; outer: for (var x = 0; x < limit; x++) { for (var y = 0; y < limit; y++) { if (x == y) continue; if (y > 5) break outer; result += y; } } return result; }''',
'numbers':'''num @FN@() { const count = 1_000; final mask = 0xff; final fraction = 1.5e-3; return (count & mask) + fraction + @N@; }''',
'comments':'''/// @WORD@ original Unicode 🌌.\nint @FN@(int value) { /* outer /* nested */ comment */ return value + @N@; } // trailing\n''',
'primary-constructor':'''class @TYPE@(final int value, {var String name = '@WORD@'}) { String label() => '$name: $value'; }''',
'private-parameter':'''class @TYPE@ { final String _name; @TYPE@({required this._name}); String get label => _name; } @TYPE@ @FN@() => @TYPE@(name: '@WORD@');''',
'dot-shorthand':'''enum @TYPE@ { idle, ready } @TYPE@ @FN@(bool value) => value ? .ready : .idle;''',
'widget':'''import 'package:flutter/widgets.dart'; class @TYPE@ extends StatelessWidget { final String title; const @TYPE@({super.key, required this.title}); @override Widget build(BuildContext context) => Column(children: [Text(title), const SizedBox(height: @N@), Text('@WORD@')]); }''',
'widget-state':'''import 'package:flutter/material.dart'; class @TYPE@ extends StatefulWidget { const @TYPE@({super.key}); @override State<@TYPE@> createState() => _State(); } class _State extends State<@TYPE@> { int count = @N@; @override Widget build(BuildContext context) => TextButton(onPressed: () => setState(() { count++; }), child: Text('$count @WORD@')); }''',
'widget-builder':'''import 'package:flutter/widgets.dart'; Widget @FN@(List<String> values) => ListView.builder(itemCount: values.length, itemBuilder: (context, index) { final value = values[index]; return Text('$index: $value @WORD@'); });''',
'wildcard':'''int @FN@(int _) { final _ = '@WORD@'; return @N@; }''',
}
WORDS='aurora bridge cosmos delta ember forest galaxy harbor island juniper kernel lumen meteor nova orbit prism quasar river solar tundra'.split()
def main():
    root=PackSpec.open('dart').dataset_root/'sources/curriculum-v1';files={}
    for index,(family,template) in enumerate(TEMPLATES.items()):
        for variant in range(24):
            rng=random.Random(92700+index*101+variant);word=WORDS[(index+variant)%len(WORDS)]
            source=template.replace('@FN@',word+'Process').replace('@TYPE@',word.title()+'Value').replace('@N@',str(rng.randrange(2,30))).replace('@WORD@',word)+'\n'
            if variant%4==1:source=source.replace('\n','\r\n')
            raw=source.encode();path=root/family/f'{variant:02}.dart';path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve previous Dart curriculum')
            if not path.exists():path.write_bytes(raw)
            files[str(path.relative_to(root))]=hashlib.sha256(raw).hexdigest()
    license=b'Original Dart syntax tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or Playground copies.\n';path=root/'LICENSE'
    if path.exists() and path.read_bytes()!=license:raise ValueError('Preserve Dart curriculum license')
    path.write_bytes(license)
    lock=dict(format='nsh-dart-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest())
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Preserve earlier Dart curriculum lock')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'original Dart tasks;',len(TEMPLATES),'families')
if __name__=='__main__':main()
