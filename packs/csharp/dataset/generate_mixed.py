"""Original bounded mixed tasks with varied indentation and modern string contexts."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
from packs.csharp.dataset.generate_curriculum import WORDS

PROGRAMS={
'html-digest':'''record {item}(string Title, int Count);
class {cls} {{
  string {method}({item} data) {{
    var content = $$"""
        <main data-kind="{word}">
          <h1>{{{{data.Title}}}}</h1>
          <!-- metadata stays in this string -->
          <p>{{{{data.Count}}}}</p>
        </main>
        """;
    return content;
  }}
}}
''',
'html-menu':'''using System.Linq;
class {cls} {{
  string {method}(string[] names) {{
    var title = string.Join(" ; ", names.Select(value => value.Trim()));
    return $"""
        <nav class="{word}">
          <span>{{title}}</span>
          <a href="/source">View source</a>
        </nav>
        """;
  }}
}}
''',
'html-invoice':'''record {item}(string Name, decimal Price);
class {cls} {{
  string {method}({item} value) => $$"""
      <article class="{word}" aria-label="invoice">
          <h2>{{{{value.Name}}}}</h2>
          <b>{{{{value.Price}}}}</b>
          <!-- class, record and return are content -->
      </article>
      """;
}}
''',
'json-envelope':'''using System.Linq;
class {cls} {{
  string {method}(string name, int count) {{
    var text = $$"""
        {{
            "name": "{{{{name}}}}",
            "count": {{{{count}}}},
            "message": "{word} with quoted text"
        }}
        """;
    return text + $" / {{name}} / {{count}}";
  }}
}}
''',
'raw-quotes':'''class {cls} {{
  string {method}() => """"
      The {word} note contains "plain quotes".
      Triple quotes """ remain part of this text.
      <tag attribute="value">content</tag>
      """";
  object Bytes() {{ var content = """{{ "flag": true }}"""u8; return content.Length; }}
}}
''',
'query-block':'''using System.Linq;
record {item}(string Name, int Score);
class {cls} {{
  public string[] {method}({item}[] source) {{
    var selected = from row in source
                   where row.Score > {n}
                   orderby row.Name
                   select row.Name;
    return selected.ToArray();
  }}
}}
''',
'query-loops':'''using System;
using System.Linq;
var values = new[] {{ {n}, {n2}, 0 }};
var selected = from number in values where number > 0 select number * 2;
foreach (var number in selected) {{ Console.WriteLine($"{word}: {{number}} / done"); }}
''',
'property-wrapper':'''#nullable enable
class {cls}<T> where T : class {{
  public T? Value {{ get; private set; }}
  public string Name {{ get; init; }} = "{word}";
  public void {method}(T value) {{ Value = value; }}
  public string Describe() => Value?.ToString() ?? Name;
}}
''',
'enum-lifecycle':'''using System;
[Flags] enum {state} {{ None = 0, Waiting = 1, Active = 2, All = Waiting | Active }}
class {cls} {{
  public {state} Current {{ get; private set; }} = {state}.None;
  public void {method}({state} next) {{ Current = next; }}
  public bool Ready => Current == {state}.Active;
}}
''',
'primary-loops':'''using System;
using System.Collections.Generic;
class {cls}(string prefix) {{
  public string Prefix {{ get; }} = prefix;
  public void {method}(IEnumerable<string> source) {{
    foreach (var entry in source) {{ Console.WriteLine($"{{Prefix}} :: {{entry}} / {word}"); }}
  }}
}}
''',
'raw-query-log':'''class {cls} {{
  string {method}(string table) {{
    var query = $$"""
        SELECT name FROM {{{{table}}}}
        WHERE status <> '{word}'
        /* inline SQL text is still a C# string */
        ORDER BY name
        """;
    return $@"Query: {{query}}";
  }}
}}
''',
'generic-output':'''using System.Collections.Generic;
using System.Linq;
record {item}(string Name, int Count);
class {cls}<T> where T : notnull {{
  readonly Dictionary<string,T> data = new();
  public void {method}(string key, T value) => data[key] = value;
  public T Get(string key) => data[key];
  public object Names() {{ var result = from pair in data select pair.Key; return result.ToArray(); }}
}}
''',
}


def main():
    root=PackSpec.open('csharp').dataset_root/'sources/mixed-v1';hashes={}
    for index,(family,template) in enumerate(PROGRAMS.items()):
        for variant in range(32):
            rng=random.Random(7019+101*index+variant);words=rng.sample(WORDS,6)
            values=dict(cls=words[0].title()+'View',item=words[1].title()+'Row',state=words[2].title()+'State',
                        method=words[3].title(),word=words[4],n=rng.randrange(2,24),n2=rng.randrange(25,99))
            source=template.format(**values)
            scale=rng.choice([1,2,4]);source='\n'.join(' '*(len(line)-len(line.lstrip()))*scale+line.lstrip() for line in source.split('\n'))
            raw=source.encode();target=root/family/f'{variant:02d}.cs';target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve existing C# mixed task')
            if not target.exists():target.write_bytes(raw)
            hashes[target.relative_to(root).as_posix()]=hashlib.sha256(raw).hexdigest()
    license=root/'LICENSE'
    if not license.exists():license.write_text('Original mixed C# tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no Golden/Playground sources copied.\n')
    lock={'format':'nsh-csharp-mixed-v1','generatorSha256':file_hash(Path(__file__)),'files':hashes};p=root/'source.lock.json'
    if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve mixed task lock')
    p.write_text(json.dumps(lock,indent=2)+'\n');print(len(hashes),'mixed C# tasks across',len(PROGRAMS),'families')


if __name__=='__main__':main()
