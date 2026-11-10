"""Independent mixed PHP/template tasks, separate from visible probes."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
from .generate_curriculum import WORDS
PROGRAMS={
'full-page':'''<?php
$summary = strtoupper($heading) . ' / {word}';
?>
<!doctype html>
<html lang="en">
<head>
<style>.{word} {{ padding: {n}px; color: #246; }}</style>
<script>const count = {n}; console.log(count + 1);</script>
</head>
<body>
<h1><?= htmlspecialchars($summary) ?></h1>
</body>
</html>
''',
'assets-and-count':'''<style>
.{word} {{ color: navy; margin: {n}px; }}
</style>
<script>
const mode = "{word}";
console.log(mode.toUpperCase());
</script>
<?php
$count = count($items);
$ready = $count > 0;
?>
<output><?= $ready ? $count : 'empty' ?></output>
''',
'widget-template':'''<?php
function {fn}(int $value): string {{ return number_format($value + {n}); }}
?>
<style>.{word} {{ display: flex; padding: {n}px; }}</style>
<script>function format(value) {{ return String(value); }}</script>
<section class="{word}">
<?php if ($value !== null): ?>
    <b><?= {fn}($value) ?></b>
<?php endif; ?>
</section>
''',
'loop-assets':'''<script>
const values = [1, 2, {n}];
console.log(values.map(value => value + 1));
</script>
<style>.{word} {{ list-style: none; }}</style>
<ul>
<?php foreach ($rows as $key => $row): ?>
    <li><?= $key . ' - ' . htmlspecialchars($row) ?></li>
<?php endforeach; ?>
</ul>
''',
'header-footer':'''<?php
$title = $data['title'] ?? '{word}';
$limit = max({n}, count($data));
?>
<header><h2><?= htmlspecialchars($title) ?></h2></header>
<script>const ready = true; console.log(ready);</script>
<style>header {{ border-bottom: 1px solid #abc; }}</style>
<footer><?= sprintf('%d entries', $limit) ?></footer>
''',
'heredoc-message':'''<?php
namespace App\\{ns};
class {cls} {{
    public function {fn}(string $name, int $count): string {{
        $message = <<<NOTE
Hello {{$name}},
There are {{$count}} {word} entries ready.
The document contains quotes "like these".
NOTE;
        return trim($message);
    }}
}}
''',
'nowdoc-configuration':'''<?php
namespace App\\{ns};
class {cls} {{
    public const DEFAULTS = <<<'CONFIG'
[{word}]
name = "$literal"
message = "Original text stays intact."
CONFIG;
    public function {fn}(): string {{ return self::DEFAULTS . "\\n"; }}
}}
''',
'interpolated-object':'''<?php
class {cls} {{
    public function __construct(public int $id, public string $name) {{}}
    public function {fn}(): string {{
        $prefix = '{word}';
        return "{{$prefix}} #{{$this->id}} / {{$this->name}}!";
    }}
}}
''',
'named-attributes':'''<?php
namespace App\\{ns};
#[Map(table: '{word}', cache: true)]
readonly class {cls} {{
    public function __construct(public string $name) {{}}
    public function {fn}(int $length): string {{
        return substr(string: $this->name, offset: 0, length: $length);
    }}
}}
''',
'enum-rendering':'''<?php
namespace App\\{ns};
enum {state}: int {{ case Draft = 0; case Live = {n}; }}
function {fn}({state} $value): string {{
    if ($value === {state}::Live) return '{word} live';
    return {state}::Draft->name;
}}
''',
'nowdoc-report':'''<?php
function {fn}(array $values): array {{
    $raw = <<<'REPORT'
The $name is not interpolated.
Escapes \\n and <tag name="{word}"> remain original text.
REPORT;
    return [$raw, count($values), '{word}'];
}}
''',
'static-factory':'''<?php
namespace App\\{ns};
final class {cls} {{
    public function __construct(private readonly string $name) {{}}
    public static function {fn}(array $data): self {{
        return new self($data['name'] ?? '{word}');
    }}
    public function label(): string {{ return "Name: {{$this->name}}"; }}
}}
''',
}
def main():
 root=PackSpec.open('php').dataset_root/'sources/mixed-v1';hashes={}
 for index,(family,template) in enumerate(PROGRAMS.items()):
  for variant in range(24):
   rng=random.Random(91337+107*index+variant);w=rng.sample(WORDS,5);source=template.format(fn=w[0]+'_render',word=w[1],ns=w[2].title(),cls=w[3].title()+'Record',state=w[4].title()+'State',n=rng.randrange(2,24));source=source.replace('    ',['    ','  ','\t'][variant%3])
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();p=root/family/f'{variant:02d}.php';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve mixed PHP source; use a new revision')
   if not p.exists():p.write_bytes(raw)
   hashes[p.relative_to(root).as_posix()]=hashlib.sha256(raw).hexdigest()
 license=root/'LICENSE'
 if not license.exists():license.write_text('Original mixed PHP and template tasks for Neural Semantic Highlighting.\nPrivate development dataset; no Golden, Playground or upstream copies.\n')
 lock={'format':'nsh-php-mixed-v1','generatorSha256':file_hash(Path(__file__)),'files':hashes};p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve original mixed lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(hashes),'PHP mixed tasks across',len(PROGRAMS),'families')
if __name__=='__main__':main()
