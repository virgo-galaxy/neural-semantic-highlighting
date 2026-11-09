"""Second original curriculum: mixed Java tasks, independent of visible probes."""
from pathlib import Path
import hashlib
import json
import random
from training.shared.spec import PackSpec, file_hash
from packs.java.dataset.generate_curriculum import WORDS

PROGRAMS = {
'job-routing': '''import java.util.*;
enum {state} {{ QUEUED, ACTIVE, STOPPED }}
sealed interface {item} permits {ok}, {bad} {{}}
record {ok}(String title) implements {item} {{}}
record {bad}(int status) implements {item} {{}}
class {cls} {{
  private {state} phase = {state}.QUEUED;
  String {method}({item} event) {{
    return switch (event) {{
      case {ok}(var title) when title.length() > {n} -> "accepted: " + title;
      case {bad}(var code) -> "status = %d".formatted(code);
      default -> "pending";
    }};
  }}
}}
''',
'permissions': '''import java.util.*;
class {cls} {{
  enum {state} {{ READ, WRITE, ADMIN }}
  private final Set<{state}> allowed = EnumSet.of({state}.READ);
  boolean {method}({state} requested) {{ return allowed.contains(requested); }}
  List<String> labels() {{ return allowed.stream().map(Enum::name).toList(); }}
}}
''',
'error-catalog': '''enum {state} {{
  UNKNOWN, INVALID, UNAVAILABLE;
  String {method}(String message) {{ return name() + " : " + message; }}
}}
class {cls} {{
  private {state} reason = {state}.UNKNOWN;
  {state} reason() {{ return reason; }}
  void reset() {{ reason = {state}.UNKNOWN; }}
}}
''',
'finite-state': '''class {cls} {{
  enum {state} {{ OFF, WARMING, ON, COOLING }}
  {state} next({state} current) {{ return switch (current) {{
    case OFF -> {state}.WARMING;
    case WARMING -> {state}.ON;
    case ON -> {state}.COOLING;
    case COOLING -> {state}.OFF;
  }}; }}
}}
''',
'annotated-record': '''import java.lang.annotation.*;
@Target(ElementType.RECORD_COMPONENT) @interface {tag} {{}}
record {item}(@{tag} String title, int priority) {{
  {item} {{ title = title.strip(); }}
  String {method}() {{ return "[ %s ] %d".formatted(title, priority); }}
}}
''',
'pair-conversion': '''import java.util.*;
import java.util.function.*;
record {item}<T>(T first, T second) {{
  <R> {item}<R> {method}(Function<T, R> fn) {{ return new {item}<>(fn.apply(first), fn.apply(second)); }}
  List<T> values() {{ return List.of(first, second); }}
}}
class {cls} {{ {item}<String> data = new {item}<>("{word}", " waiting "); }}
''',
'qualified-methods': '''import java.util.*;
import java.util.function.*;
class {cls} {{
  private final List<String> names;
  {cls}(List<String> source) {{ names = source; }}
  void {method}(Consumer<String> out) {{ names.forEach(out::accept); }}
  List<String> cleaned() {{ return names.stream().map(String::strip).toList(); }}
  Supplier<List<String>> factory = ArrayList::new;
}}
''',
'event-filtering': '''import java.util.*;
record {item}(String title, int weight) {{}}
class {cls} {{
  String {method}(Object value) {{
    if (value instanceof {item}(var name, var size) && size > {n}) return name;
    if (value instanceof String name) return name.strip();
    return "unsupported";
  }}
}}
''',
'query-building': '''class {cls} {{
  private final String table = "{word}";
  String {method}(int offset) {{
    String sql = """
        SELECT id, title
        FROM %s
        WHERE enabled = true AND id > %d
        /* a query comment remains string content */
        ORDER BY title
        """;
    return sql.formatted(table, offset);
  }}
}}
''',
'email-rendering': '''record {item}(String subject, String recipient) {{
  String {method}() {{ return """
      <main data-kind="{word}">
        <h1>%s</h1>
        <p>Hello, %s</p>
      </main>
      """.formatted(subject, recipient); }}
}}
''',
'page-layout': '''class {cls} {{
  static final String HEAD = """
      <!doctype html>
      <html><head><meta charset="utf-8"></head>
      <body>
      """;
  String {method}(String content) {{
    String footer = """
        <footer>{word}</footer>
        </body></html>
        """;
    return HEAD + content + footer;
  }}
}}
''',
'document-template': '''class {cls} {{
  String {method}(String author) {{
    return """
        # {word} notes

        Class, record and enum are ordinary text here.
        Owner: %s
        Quoted: "plain" and 'literal'
        """.formatted(author);
  }}
}}
''',
'quote-table': '''class {cls} {{
  String[] data = {{" ", "  ", " a b ", ": ", " / ", " -- ", "{word}"}};
  String {method}(String input) {{ return String.join(" ; ", data) + " | " + input; }}
  char quote = '\\"';
  String escaped = "\\\"a b\\\"";
}}
''',
'json-config': '''class {cls} {{
  String {method}(String user, int version) {{ return """
      {{
        "name": "%s",
        "version": %d,
        "message": "{word} with spaces",
        "enabled": true
      }}
      """.formatted(user, version); }}
}}
''',
'module-providers': '''module app.{word} {{
  requires java.base;
  requires static java.sql;
  exports app.{word}.api;
  uses app.{word}.{item};
  provides app.{word}.{item} with app.{word}.{ok}, app.{word}.{bad};
}}
''',
'module-bridge': '''module lib.{word} {{
  requires transitive java.net.http;
  requires java.logging;
  exports lib.{word}.internal to framework.core, client.app;
  opens lib.{word}.model to mapper.core;
  uses lib.{word}.{item};
}}
''',
'module-driver': '''open module driver.{word} {{
  requires transitive java.sql;
  provides java.sql.Driver with driver.{word}.{cls};
  exports driver.{word}.api;
}}
''',
'module-plugins': '''module plugin.{word} {{
  requires java.logging;
  requires static java.compiler;
  opens plugin.{word}.internal;
  uses plugin.{word}.api.{item};
  provides plugin.{word}.api.{item} with plugin.{word}.internal.{cls};
}}
''',
}


def main():
    root = PackSpec.open('java').dataset_root / 'sources/mixed-v1'
    hashes = {}
    for i, (family, template) in enumerate(PROGRAMS.items()):
        for j in range(32):
            rng = random.Random(6101 + i * 101 + j)
            words = rng.sample(WORDS, 9)
            params = {key: words[index].title() + suffix for index, (key, suffix) in enumerate([
                ('cls', 'Manager'), ('state', 'Phase'), ('item', 'Event'), ('ok', 'Ready'), ('bad', 'Failed'), ('tag', 'Hint')])}
            params.update(method=words[6], word=words[7], n=rng.randrange(1, 20))
            raw = template.format(**params).encode()
            target = root / family / f'{j:02d}.java'; target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != raw: raise ValueError('Preserve existing mixed curriculum')
            if not target.exists(): target.write_bytes(raw)
            hashes[target.relative_to(root).as_posix()] = hashlib.sha256(raw).hexdigest()
    license = root / 'LICENSE'
    if not license.exists(): license.write_text('Original mixed Java syntax tasks authored for Neural Semantic Highlighting.\nPrivate development data. No Golden, Playground or upstream examples are copied.\n')
    identity = {'format': 'nsh-java-mixed-v1', 'generatorSha256': file_hash(Path(__file__)), 'files': hashes}
    path = root / 'source.lock.json'
    if path.exists() and json.loads(path.read_text()) != identity: raise ValueError('Preserve mixed curriculum lock')
    path.write_text(json.dumps(identity, indent=2) + '\n')
    print('Mixed Java:', len(hashes), 'tasks across', len(PROGRAMS), 'families')


if __name__ == '__main__': main()
