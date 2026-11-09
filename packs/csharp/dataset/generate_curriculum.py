"""Original mixed C# tasks, kept separate from Golden and Playground probes."""
from pathlib import Path
import hashlib
import json
import random
from training.shared.spec import PackSpec, file_hash

TEMPLATES = {
'objects': '''namespace Demo.{ns};
public sealed class {cls} {{
  private readonly string {field};
  public {cls}(string {arg}) {{ {field} = {arg}; }}
  public string {method}() => {field}.Trim();
}}
''',
'properties': '''public class {cls} {{
  public required string Name {{ get; init; }}
  public int {prop} {{ get; private set; }}
  public void {method}(int {arg}) {{ {prop} += {arg}; }}
}}
''',
'generics': '''using System.Collections.Generic;
class {cls}<T> where T : notnull {{
  private readonly Dictionary<string, T> {field} = new();
  public void {method}(string key, T {arg}) {{ {field}[key] = {arg}; }}
  public T Get(string key) => {field}[key];
}}
''',
'interfaces': '''interface {iface}<out T> {{ T {method}(); }}
class {cls}(string {arg}) : {iface}<string> {{
  public string {method}() => {arg}.Trim();
}}
''',
'records': '''namespace Demo.{ns};
public record {item}(string Name, int Count) {{
  public bool Ready => Count > {n};
  public string {method}() => $"{{Name}}: {{Count}}";
}}
class {cls} {{ {item} copy({item} value) => value with {{ Count = value.Count + 1 }}; }}
''',
'record-struct': '''public readonly record struct {item}(double X, double Y) {{
  public double {method}() => X * X + Y * Y;
  public {item} Move(double dx, double dy) => new(X + dx, Y + dy);
}}
''',
'primary-constructor': '''class {cls}(string {arg}, int limit) {{
  private readonly string {field} = {arg}.Trim();
  public string {method}(int count) => count > limit ? {field} : "{word}";
}}
''',
'structs': '''public readonly struct {item} {{
  public readonly int {prop};
  public {item}(int {arg}) {{ {prop} = {arg}; }}
  public int {method}() => {prop} * {n};
}}
''',
'enum-state': '''enum {state} {{ Pending, Active = {n}, Complete }}
class {cls} {{
  private {state} {field} = {state}.Pending;
  void {method}() {{ {field} = {state}.Active; }}
  bool Ready => {field} == {state}.Complete;
}}
''',
'enum-flags': '''using System;
[Flags] enum {state} {{ None = 0, Read = 1, Write = 2, All = Read | Write }}
class {cls} {{ bool {method}({state} {arg}) => ({arg} & {state}.Write) != 0; }}
''',
'attributes': '''using System;
[AttributeUsage(AttributeTargets.Method)]
sealed class {tag} : Attribute {{ public string Name {{ get; set; }} = "{word}"; }}
class {cls} {{
  [{tag}(Name = "{word}")]
  public void {method}() {{}}
}}
''',
'nullable': '''#nullable enable
class {cls} {{
  public string? {prop} {{ get; set; }}
  public string {method}() => {prop}?.Trim() ?? "{word}";
  public void Set(string? {arg}) {{ {prop} ??= {arg}; }}
}}
''',
'lambdas': '''using System;
using System.Linq;
class {cls} {{
  string[] {method}(string[] {arg}) => {arg}
    .Where(value => !string.IsNullOrWhiteSpace(value))
    .Select(value => value.Trim()).OrderBy(value => value).ToArray();
}}
''',
'lambda-block': '''using System;
class {cls} {{
  Func<int, int> {field} = (int {arg}) => {{ int total = {arg} + {n}; return total; }};
  int {method}(int count) => {field}(count);
}}
''',
'local-functions': '''int {method}(int {arg}) {{
  int Scale(int value) => value * {n};
  return Scale({arg}) + Scale({n2});
}}
var result = {method}({n});
System.Console.WriteLine(result);
''',
'async-tasks': '''using System.Threading;
using System.Threading.Tasks;
class {cls} {{
  async Task<string> {method}(string {arg}, CancellationToken token) {{
    await Task.Delay({n}, token);
    return {arg}.Trim();
  }}
}}
''',
'async-stream': '''using System.Collections.Generic;
using System.Threading.Tasks;
class {cls} {{
  async IAsyncEnumerable<int> {method}() {{
    for (int index = 0; index < {n}; index++) {{ await Task.Yield(); yield return index; }}
  }}
}}
''',
'linq-query': '''using System.Linq;
record {item}(string Name, int Score);
class {cls} {{
  object {method}({item}[] {arg}) =>
    from value in {arg}
    where value.Score >= {n}
    orderby value.Name
    select new {{ value.Name, Rank = value.Score + 1 }};
}}
''',
'linq-join': '''using System.Linq;
class {cls} {{
  object {method}(int[] left, int[] right) =>
    from a in left join b in right on a equals b
    let total = a + b where total > {n} select total;
}}
''',
'linq-group': '''using System.Linq;
class {cls} {{
  object {method}(string[] {arg}) =>
    from text in {arg} group text by text.Length into lengths
    orderby lengths.Key descending select new {{ Length = lengths.Key, Count = lengths.Count() }};
}}
''',
'patterns': '''record {item}(string Name, int Count);
class {cls} {{
  string {method}(object {arg}) => {arg} switch {{
    {item}(var name, > {n}) => name,
    string text when text.Length > 0 => text,
    null => "missing", _ => "{word}"
  }};
}}
''',
'pattern-properties': '''class {cls} {{
  bool {method}(object {arg}) => {arg} is string {{ Length: > {n} }} text && text.StartsWith("{word}");
  int Size(object input) {{ if (input is int count and > 0) return count; return 0; }}
}}
''',
'list-patterns': '''class {cls} {{
  int {method}(int[] {arg}) {{
    if ({arg} is [var first, ..] && {arg}.Length > {n}) return first;
    return {arg} is [] ? 0 : -1;
  }}
}}
''',
'collections': '''using System.Collections.Generic;
class {cls} {{
  int[] {field} = [{n}, {n2}, 0];
  int[] {method}(int[] {arg}) => [.. {field}, .. {arg}];
  List<string> Names() => ["{word}", "ready"];
}}
''',
'ranges': '''class {cls} {{
  string {method}(string {arg}) {{
    var middle = {arg}[1..^1];
    var head = {arg}[..{n}];
    return head + " : " + middle;
  }}
}}
''',
'raw-html': '''class {cls} {{
  string {method}() => """
      <section class="{word}">
        <h2>Source display</h2>
        <!-- string content -->
      </section>
      """;
}}
''',
'raw-sql': '''class {cls} {{
  string {field} = """
      SELECT name, total FROM {word}
      WHERE enabled = 1
      ORDER BY name
      """;
  string {method}() => {field}.Trim();
}}
''',
'raw-json': '''class {cls} {{
  string {method}(string {arg}) => $$"""
      {{ "name": "{{{{{arg}}}}}", "count": {n},
         "ready": true, "note": "{word}" }}
      """;
}}
''',
'raw-diagnostics': '''record {item}(string Name, int Code) {{
  string {method}() => $"""
      {word}: {{Name}}
      status = {{Code}}
      record, class and return are ordinary text
      """;
}}
''',
'verbatim': '''class {cls} {{
  string root = @"C:\\Data\\{word}\\";
  string query = @"SELECT ""name"" FROM ""{word}""";
  string {method}(string {arg}) => $@"{{root}}\\{{{arg}}}";
}}
''',
'interpolation': '''class {cls} {{
  string {method}(string {arg}, int count) =>
    $"Name: {{{arg},-12}} | total: {{count:000}} | {{(count > {n} ? "yes" : "no")}}";
}}
''',
'utf8': '''class {cls} {{
  object {method}() {{
    var bytes = "{word}"u8;
    var raw = """{{ "value": {n} }}"""u8;
    return bytes.Length + raw.Length;
  }}
}}
''',
'string-spacing': '''class {cls} {{
  string[] {field} = [" ", " a b ", " : ", " / ", "{word}"];
  string {method}(string {arg}) => string.Join(" ; ", {field}) + " | " + {arg};
  char quote = '\\"'; char slash = '\\\\';
}}
''',
'directives': '''#nullable enable
#define FEATURE_{upper}
#if FEATURE_{upper}
namespace Demo.{ns};
class {cls} {{ public string {prop} {{ get; init; }} = "{word}"; }}
#else
class {other} {{}}
#endif
''',
'directive-regions': '''#region {word} source
#pragma warning disable CS0169
class {cls} {{
  private int {field};
  public int {method}() => {n};
}}
#pragma warning restore CS0169
#endregion
''',
'directive-branches': '''#if DEBUG
class {cls} {{ int {method}() => {n}; }}
#elif TRACE
class {other} {{ string Name => "{word}"; }}
#else
class {item} {{ bool Ready => false; }}
#endif
''',
'events': '''using System;
class {cls} {{
  public event Action<int>? Changed;
  private int {field};
  public void {method}(int {arg}) {{ {field} = {arg}; Changed?.Invoke({field}); }}
}}
''',
'delegates': '''delegate int {item}(int value);
class {cls} {{
  {item} {field} = value => value * {n};
  int {method}(int {arg}) => {field}({arg});
}}
''',
'loops': '''class {cls} {{
  int {method}(int[] {arg}) {{
    int total = 0;
    foreach (int value in {arg}) {{ if (value > {n}) total += value; }}
    for (int i = 0; i < {arg}.Length; i++) total ^= {arg}[i];
    return total;
  }}
}}
''',
'exceptions': '''using System;
class {cls} {{
  int {method}(string {arg}) {{
    try {{ return int.Parse({arg}); }}
    catch (FormatException error) when ({arg}.Length > {n}) {{ Console.WriteLine(error.Message); return -1; }}
    finally {{ Console.WriteLine("{word}"); }}
  }}
}}
''',
'resources': '''using System.IO;
class {cls} {{
  string {method}(string {arg}) {{ using var stream = new StreamReader({arg}); return stream.ReadToEnd(); }}
}}
''',
'async-disposal': '''using System.IO;
using System.Threading.Tasks;
class {cls} {{
  async Task<int> {method}(Stream {arg}) {{
    await using var output = new MemoryStream();
    await {arg}.CopyToAsync(output);
    return (int)output.Length;
  }}
}}
''',
'out-binding': '''class {cls} {{
  int {method}(string {arg}) {{
    if (int.TryParse({arg}, out var value)) return value;
    return {n};
  }}
}}
''',
'generics-constraints': '''using System;
interface {iface}<T> where T : class {{ T {method}(); }}
class {cls}<T> : {iface}<T> where T : class, new() {{
  public T {method}() => new T();
  public bool IsReady(object {arg}) => {arg} is T;
}}
''',
'operators': '''readonly struct {item}(int value) {{
  public readonly int Value = value;
  public static {item} operator +({item} left, {item} right) => new(left.Value + right.Value);
  public static implicit operator int({item} {arg}) => {arg}.Value;
}}
''',
'inheritance': '''abstract class {other} {{ public abstract string {method}(); }}
sealed class {cls}(string {arg}) : {other} {{
  public override string {method}() => {arg};
  public override string ToString() => {method}();
}}
''',
'partial-types': '''partial class {cls} {{ partial void {method}(int count); }}
partial class {cls} {{
  private int {field};
  partial void {method}(int count) {{ {field} += count; }}
}}
''',
'unicode': '''// 原始代码 🌙 {word}
class {cls} {{
  string 标题 = "星空 🌌 {word}";
  string {method}(string {arg}) => 标题 + {arg};
}}
''',
'object-initializers': '''record {item} {{ public required string Name {{ get; init; }} public int Count {{ get; init; }} }}
class {cls} {{
  {item} {method}(string {arg}) => new() {{ Name = {arg}, Count = {n} }};
  {item} Next({item} value) => value with {{ Count = value.Count + 1 }};
}}
''',
'attributes-generic': '''using System;
[AttributeUsage(AttributeTargets.Class)] class {tag}(string name) : Attribute {{}}
[{tag}("{word}")]
class {cls}<T>(T {arg}) {{ public T {prop} => {arg}; }}
''',
}
WORDS='atlas cedar delta ember flora glade harbor ivory jade kernel lagoon maple nova orbit prism quartz river solar tundra umber violet willow xenon yellow zenith aurora breeze canyon dawn echo forest grove horizon iris juniper meadow north opal pine'.split()


def main():
    root=PackSpec.open('csharp').dataset_root/'sources/curriculum-v3';hashes={}
    for index,(family,template) in enumerate(TEMPLATES.items()):
        for variant in range(24):
            rng=random.Random(8153+101*index+variant);words=rng.sample(WORDS,10)
            values=dict(cls=words[0].title()+'Service',other=words[1].title()+'Base',item=words[2].title()+'Entry',
                        iface='I'+words[3].title()+'Store',state=words[4].title()+'State',tag=words[5].title()+'Attribute',
                        field=words[6],prop=words[6].title(),arg=words[7],method=words[8].title(),word=words[9],
                        ns=words[9].title(),upper=words[9].upper(),n=rng.randrange(2,24),n2=rng.randrange(25,99))
            source=template.format(**values)
            if family=='unicode' and variant%2:source=source.replace('\n','\r\n')
            raw=source.encode('utf-8');target=root/family/f'{variant:02d}.cs';target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve existing C# curriculum; use a new revision')
            if not target.exists():target.write_bytes(raw)
            hashes[target.relative_to(root).as_posix()]=hashlib.sha256(raw).hexdigest()
    license=root/'LICENSE'
    if not license.exists():license.write_text('Original C# syntax tasks authored for Neural Semantic Highlighting.\nPrivate development dataset. No Golden/Playground or upstream examples are copied.\n')
    lock={'format':'nsh-csharp-curriculum-v3','generatorSha256':file_hash(Path(__file__)),'files':hashes}
    p=root/'source.lock.json'
    if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve existing curriculum lock')
    p.write_text(json.dumps(lock,indent=2)+'\n');print(len(hashes),'C# tasks across',len(TEMPLATES),'families')


if __name__=='__main__':main()
