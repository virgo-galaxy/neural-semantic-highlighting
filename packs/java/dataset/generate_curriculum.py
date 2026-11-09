"""Original bounded Java syntax tasks; Golden and Playground are never collected."""
from pathlib import Path
import hashlib
import json
import random

from training.shared.spec import PackSpec, file_hash

# All renamed/literal variants of a task keep the same family before windowing.
TEMPLATES = {
    'fields': '''package demo.{pkg};
public final class {cls} {{
  private final String {field};
  public {cls}(String {arg}) {{ this.{field} = {arg}; }}
  public String {method}() {{ return {field}.trim(); }}
}}
''',
    'collections': '''import java.util.*;
class {cls}<T extends Comparable<T>> {{
  private final List<T> {field} = new ArrayList<>();
  void {method}(T {arg}) {{ {field}.add({arg}); }}
  List<T> sorted() {{ return {field}.stream().sorted().toList(); }}
}}
''',
    'interfaces': '''interface {cls}<T> {{ T {method}(String {arg}); }}
final class {other} implements {cls}<String> {{
  @Override public String {method}(String {arg}) {{ return {arg}.strip(); }}
}}
''',
    'enum': '''enum {cls} {{
  READY({n}), RUNNING({n2}), DONE(0);
  private final int {field};
  {cls}(int {arg}) {{ {field} = {arg}; }}
  int {method}() {{ return {field}; }}
}}
''',
    'annotation': '''import java.lang.annotation.*;
@Retention(RetentionPolicy.RUNTIME)
@interface {cls} {{ String value() default "{word}"; }}
@{cls}("{word}") final class {other} {{ @Deprecated void {method}() {{}} }}
''',
    'lambda-stream': '''import java.util.*;
class {cls} {{
  List<String> {method}(List<String> {arg}) {{
    return {arg}.stream().filter(item -> !item.isBlank()).map(String::trim).toList();
  }}
}}
''',
    'lambda-block': '''import java.util.function.*;
class {cls} {{
  Function<String, Integer> {field} = (String {arg}) -> {{
    int total = {arg}.length() + {n}; return total;
  }};
  int {method}(String input) {{ return {field}.apply(input); }}
}}
''',
    'try-resources': '''import java.io.*;
import java.nio.file.*;
class {cls} {{
  String {method}(Path {arg}) throws IOException {{
    try (BufferedReader input = Files.newBufferedReader({arg})) {{ return input.readLine(); }}
    catch (IOException error) {{ throw new IOException("{word}", error); }}
  }}
}}
''',
    'loops': '''class {cls} {{
  int {method}(int[] {arg}) {{
    int sum = 0;
    for (int item : {arg}) {{ if (item > {n}) sum += item; }}
    for (int i = 0; i < {arg}.length; i++) sum ^= {arg}[i];
    return sum;
  }}
}}
''',
    'numbers': '''class {cls} {{
  static final long {field} = 0xff_00L;
  double {method}(double {arg}) {{ return {arg} * 0x1.8p2 + 1.25e-3 - {n}.0; }}
  int bits(int value) {{ return (value >>> 2) & 0b1010_0110; }}
}}
''',
    'strings': '''class {cls} {{
  String {field} = "{word}\\n\\\"quoted\\\"";
  char slash = '\\\\';
  String {method}(String {arg}) {{ return "<" + {arg} + ">"; }}
}}
''',
    'javadoc': '''/** A {word} source with original documentation.
 * @param <T> item type
 */
class {cls}<T> {{
  // record and return are comment text
  T {field}; /* nullable field */
  T {method}() {{ return {field}; }}
}}
''',
    'record-model': '''package demo.{pkg};
import java.util.*;
public record {cls}(String {field}, int count) {{
  public {cls} {{ {field} = Objects.requireNonNull({field}).strip(); }}
  public String {method}() {{ return {field} + ":" + count; }}
}}
''',
    'record-generic': '''import java.util.function.*;
record {cls}<T>(T {field}) {{
  <R> {cls}<R> {method}(Function<T, R> {arg}) {{ return new {cls}<>({arg}.apply({field})); }}
}}
''',
    'record-nested': '''class {cls} {{
  record {other}(String {field}, boolean enabled) {{}}
  {other} {method}(String {arg}) {{ return new {other}({arg}, true); }}
}}
''',
    'sealed-record': '''sealed interface {cls} permits {other}, {third} {{}}
record {other}(String {field}) implements {cls} {{}}
record {third}(int count) implements {cls} {{}}
class {fourth} {{
  String {method}({cls} {arg}) {{ return switch ({arg}) {{
    case {other}(var text) -> text;
    case {third}(var count) -> Integer.toString(count);
  }}; }}
}}
''',
    'sealed-class': '''sealed abstract class {cls} permits {other}, {third} {{ abstract int {method}(); }}
non-sealed class {other} extends {cls} {{ int {method}() {{ return {n}; }} }}
final class {third} extends {cls} {{ int {method}() {{ return {n2}; }} }}
''',
    'sealed-generic': '''sealed interface {cls}<T> permits {other}, {third} {{}}
record {other}<T>(T {field}) implements {cls}<T> {{}}
record {third}<T>(String reason) implements {cls}<T> {{}}
''',
    'instanceof': '''class {cls} {{
  int {method}(Object {arg}) {{
    if ({arg} instanceof String text && !text.isBlank()) return text.length();
    if ({arg} instanceof Integer value) return value + {n};
    return -1;
  }}
}}
''',
    'guarded-switch': '''class {cls} {{
  String {method}(Object {arg}) {{ return switch ({arg}) {{
    case null -> "missing";
    case String text when text.length() > {n} -> text.substring(0, {n});
    case String text -> text;
    default -> {arg}.toString();
  }}; }}
}}
''',
    'nested-pattern': '''record {cls}(String {field}, int count) {{}}
record {other}({cls} value) {{}}
class {third} {{ int {method}(Object {arg}) {{ return switch ({arg}) {{
  case {other}({cls}(var text, var count)) when count > {n} -> text.length();
  default -> 0;
}}; }} }}
''',
    'switch-yield': '''class {cls} {{
  int {method}(String {arg}) {{ return switch ({arg}) {{
    case "{word}", "ready" -> {n};
    case "idle" -> {{ int total = {arg}.length(); yield total + {n2}; }}
    default -> 0;
  }}; }}
}}
''',
    'text-html': '''class {cls} {{
  String {method}(String {arg}) {{
    String {field} = """
        <article class="{word}">
          <h2>%s</h2>
          <!-- not a Java comment -->
        </article>
        """;
    return {field}.formatted({arg});
  }}
}}
''',
    'text-sql': '''record {cls}(int {field}) {{
  String {method}() {{ return """
      SELECT name, count FROM {word}
      WHERE id = %d AND status != 'class'
      ORDER BY name
      """.formatted({field}); }}
}}
''',
    'text-json': '''class {cls} {{
  static final String {field} = """
      {{"name": "{word}", "ready": true,
       "items": [1, 2, 3]}}
      """;
  String {method}() {{ return {field}.stripIndent(); }}
}}
''',
    'module-api': '''module demo.{pkg} {{
  requires java.base;
  requires transitive java.sql;
  exports demo.{pkg}.api to client.{word};
  opens demo.{pkg}.internal;
}}
''',
    'module-service': '''module service.{pkg} {{
  requires static java.logging;
  uses demo.{pkg}.{cls};
  provides demo.{pkg}.{cls} with demo.{pkg}.{other};
}}
''',
    'module-open': '''open module data.{pkg} {{
  requires java.net.http;
  exports data.{pkg};
  uses data.{pkg}.{cls};
}}
''',
    'contextual-names': '''class {cls} {{
  int record = {n}, sealed = {n2}, permits = 0;
  String yield = "{word}", when = "done";
  int {method}(int module) {{ var result = module + record; return result + sealed; }}
}}
''',
    'unicode': '''// 原始 Unicode 🌙 {word}
class {cls} {{
  String 标题 = "星空 🌌 {word}";
  String {method}(String {arg}) {{ return 标题 + {arg}; }}
}}
''',
    'arrays': '''class {cls} {{
  int[][] {field} = new int[][] {{{{{n}, {n2}}}, {{0, 1}}}};
  int {method}(int... {arg}) {{ return {arg}.length == 0 ? 0 : {arg}[0]; }}
}}
''',
    'method-ref': '''import java.util.*;
import java.util.function.*;
class {cls} {{
  Supplier<List<String>> {field} = ArrayList::new;
  void {method}(List<String> {arg}) {{ {arg}.forEach(System.out::println); }}
}}
''',
    'synchronized': '''class {cls} {{
  private volatile int {field};
  synchronized int {method}(int {arg}) {{ {field} += {arg}; return {field}; }}
  void reset() {{ synchronized (this) {{ {field} = 0; }} }}
}}
''',
    'annotation-generics': '''import java.lang.annotation.*;
@Target(ElementType.TYPE_USE) @interface {other} {{}}
class {cls}<T extends Comparable<T>> {{
  java.util.List<@{other} String> {field};
  <R extends T> R {method}(R {arg}) {{ return {arg}; }}
}}
''',
    'exception-flow': '''class {cls} {{
  String {method}(String {arg}) {{
    try {{ if ({arg} == null) throw new IllegalArgumentException("{word}"); return {arg}.trim(); }}
    catch (IllegalArgumentException | IllegalStateException error) {{ return error.getMessage(); }}
    finally {{ System.out.println("complete"); }}
  }}
}}
''',
    'inner-class': '''class {cls} {{
  private int {field} = {n};
  class {other} {{ int {method}() {{ return {cls}.this.{field}; }} }}
  Runnable task = new Runnable() {{ @Override public void run() {{ System.out.println({field}); }} }};
}}
''',
}
WORDS = 'atlas cedar delta ember flora glade harbor ivory jade kernel lagoon maple nova orbit prism quartz river solar tundra umber violet willow xenon yellow zenith aurora breeze canyon dawn echo forest grove horizon iris juniper meadow north opal pine'.split()


def main():
    root = PackSpec.open('java').dataset_root / 'sources/curriculum-v1'
    manifest = {}
    for index, (family, template) in enumerate(TEMPLATES.items()):
        for variant in range(24):
            rng = random.Random(1729 + 97 * index + variant)
            words = rng.sample(WORDS, 10)
            params = dict(cls=words[0].title() + 'Entry', other=words[1].title() + 'State', third=words[2].title() + 'Result',
                          fourth=words[3].title() + 'View', pkg=words[4], field=words[5], method=words[6],
                          arg=words[7], word=words[8], n=rng.randrange(2, 24), n2=rng.randrange(25, 99))
            source = template.format(**params)
            if family == 'unicode' and variant % 2: source = source.replace('\n', '\r\n')
            raw = source.encode('utf-8')
            target = root / family / f'{variant:02d}.java'
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != raw: raise ValueError('Preserve existing Java curriculum; use a new revision')
            if not target.exists(): target.write_bytes(raw)
            manifest[target.relative_to(root).as_posix()] = hashlib.sha256(raw).hexdigest()
    license = root / 'LICENSE'
    if not license.exists(): license.write_text('Original Java grammar tasks authored for Neural Semantic Highlighting.\nNo upstream source or independent Golden/Playground examples are copied here.\nPrivate development dataset; not published.\n')
    identity = {'format': 'nsh-java-curriculum-v1', 'generatorSha256': file_hash(Path(__file__)), 'files': manifest}
    path = root / 'source.lock.json'
    if path.exists() and json.loads(path.read_text()) != identity: raise ValueError('Preserve curriculum identity')
    path.write_text(json.dumps(identity, indent=2) + '\n')
    print('Java focused tasks:', len(manifest), 'across', len(TEMPLATES), 'families')


if __name__ == '__main__': main()
