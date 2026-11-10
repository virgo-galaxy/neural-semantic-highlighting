"""Original PHP syntax/templates; all variants keep one task family."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash

TEMPLATES={
'function':'''<?php
function {fn}(int $value, int $limit): int {{
    $total = $value + {n};
    return $total > $limit ? $total : $limit;
}}
''',
'namespace':'''<?php
namespace App\\{ns};
function {fn}(string $name): string {{
    return '{word}: ' . trim($name);
}}
''',
'class':'''<?php
namespace App\\{ns};
final class {cls} {{
    private int $count = {n};
    public function {fn}(int $amount): int {{
        $this->count += $amount;
        return $this->count;
    }}
}}
''',
'promotion':'''<?php
namespace App\\{ns};
final class {cls} {{
    public function __construct(public readonly string $name, private int $count = {n}) {{}}
    public function {fn}(): string {{ return $this->name . $this->count; }}
}}
''',
'interface':'''<?php
namespace App\\{ns};
interface {iface} {{ public function {fn}(int $id): string; }}
final class {cls} implements {iface} {{
    public function {fn}(int $id): string {{ return '{word}' . $id; }}
}}
''',
'inheritance':'''<?php
abstract class {base} {{ abstract public function {fn}(): int; }}
final class {cls} extends {base} {{
    public function {fn}(): int {{ return {n}; }}
}}
''',
'trait':'''<?php
trait {trait} {{
    protected string $name = '{word}';
    public function {fn}(): string {{ return $this->name; }}
}}
class {cls} {{ use {trait}; }}
''',
'enum-backed':'''<?php
namespace App\\{ns};
enum {state}: string {{ case Pending = 'pending'; case Ready = 'ready'; }}
function {fn}({state} $state): bool {{ return $state === {state}::Ready; }}
''',
'enum-unit':'''<?php
enum {state} {{ case North; case South; }}
function {fn}({state} $value): string {{
    return match ($value) {{ {state}::North => '{word}', {state}::South => 'south' }};
}}
''',
'class-constants':'''<?php
class {cls} {{
    public const LIMIT = {n2};
    private const NAME = '{word}';
    public static function {fn}(int $value): bool {{ return $value < self::LIMIT; }}
}}
''',
'static-call':'''<?php
class {cls} {{
    public static function create(string $name): self {{ return new self(); }}
    public static function {fn}(): self {{ return self::create('{word}'); }}
}}
''',
'import-alias':'''<?php
namespace App\\{ns};
use Domain\\{base} as Storage;
final class {cls} {{
    public function {fn}(Storage $store): array {{ return $store->load('{word}'); }}
}}
''',
'import-function':'''<?php
namespace App\\{ns};
use function Vendor\\Text\\normalize;
use const Vendor\\LIMIT;
function {fn}(string $text): string {{ return normalize($text) . LIMIT; }}
''',
'nullable':'''<?php
function {fn}(?string $name): string {{
    return $name !== null ? trim($name) : '{word}';
}}
''',
'union-types':'''<?php
function {fn}(string|int $value): string|false {{
    return is_int($value) ? (string)($value + {n}) : trim($value);
}}
''',
'intersection-types':'''<?php
function {fn}(Countable&Iterator $values): int {{
    return count($values) + {n};
}}
''',
'arrays':'''<?php
function {fn}(string $name): array {{
    $data = ['name' => $name, 'limit' => {n2}, 'active' => true];
    $data['count'] = {n};
    return $data;
}}
''',
'array-spread':'''<?php
function {fn}(array $values): array {{
    $extra = ['{word}', {n}];
    return [...$values, ...$extra];
}}
''',
'destructuring':'''<?php
function {fn}(array $pairs): int {{
    [$left, $right] = $pairs;
    return $left + $right + {n};
}}
''',
'foreach':'''<?php
function {fn}(array $values): int {{
    $total = {n};
    foreach ($values as $key => $value) {{ $total += $value; }}
    return $total;
}}
''',
'loops':'''<?php
function {fn}(int $limit): int {{
    $total = 0;
    for ($i = 0; $i < $limit; $i++) {{
        if ($i % {n} === 0) continue;
        $total += $i;
    }}
    return $total;
}}
''',
'match':'''<?php
function {fn}(int $status): string {{
    return match ($status) {{
        200, 201 => '{word} ready',
        404 => 'not found',
        default => 'unknown',
    }};
}}
''',
'closure':'''<?php
function {fn}(array $values, int $offset): array {{
    $map = function (int $value) use ($offset): int {{ return $value + $offset; }};
    return array_map($map, $values);
}}
''',
'arrow':'''<?php
function {fn}(array $values): array {{
    return array_map(fn(int $value): int => $value * {n}, $values);
}}
''',
'closure-reference':'''<?php
function {fn}(): int {{
    $count = {n};
    $increment = function () use (&$count): void {{ $count++; }};
    $increment();
    return $count;
}}
''',
'named-arguments':'''<?php
function {fn}(string $text): string {{
    return htmlspecialchars(string: $text, double_encode: false);
}}
''',
'nullsafe':'''<?php
function {fn}(?{cls} $user): string {{
    return $user?->profile()?->name ?? '{word}';
}}
''',
'coalescing':'''<?php
function {fn}(array $data): string {{
    $data['name'] ??= '{word}';
    return $data['name'] ?? 'empty';
}}
''',
'attributes':'''<?php
namespace App\\{ns};
#[Route('/{word}')]
class {cls} {{
    #[Deprecated('Use the new handler')]
    public function {fn}(): int {{ return {n}; }}
}}
''',
'exceptions':'''<?php
function {fn}(string $text): array {{
    try {{ return json_decode($text, associative: true, flags: JSON_THROW_ON_ERROR); }}
    catch (JsonException $error) {{ return ['error' => $error->getMessage()]; }}
    finally {{ $done = true; }}
}}
''',
'generator':'''<?php
function {fn}(array $values): Generator {{
    foreach ($values as $index => $value) {{ yield $index => $value + {n}; }}
}}
''',
'yield-from':'''<?php
function {fn}(iterable $values): Generator {{
    yield '{word}';
    yield from $values;
}}
''',
'interpolation':'''<?php
function {fn}(string $name, int $count): string {{
    return "Hello {{$name}}, you have {{$count}} {word} items.";
}}
''',
'complex-interpolation':'''<?php
function {fn}(array $data): string {{
    return "Name: {{$data['name']}} / {{$_SERVER['HOST']}} / {word}";
}}
''',
'heredoc':'''<?php
function {fn}(string $name): string {{
    return <<<MESSAGE
Hello $name,
The {word} document is ready.
MESSAGE;
}}
''',
'heredoc-html':'''<?php
function {fn}(string $title): string {{
    return <<<PAGE
<section class="{word}">
    <h2>{{$title}}</h2>
    <p>Quoted text stays in this string.</p>
</section>
PAGE;
}}
''',
'nowdoc':'''<?php
function {fn}(): string {{
    return <<<'RAW'
The $variable and "quotes" are literal {word} text.
No PHP expression executes here.
RAW;
}}
''',
'nowdoc-code':'''<?php
const {upper}_SOURCE = <<<'CODE'
function example($name) {{
    return "quoted $name";
}}
CODE;
function {fn}(): string {{ return {upper}_SOURCE; }}
''',
'heredoc-query':'''<?php
function {fn}(int $limit): string {{
    $query = <<<SQL
SELECT name, count
FROM {word}_items
WHERE count < $limit
ORDER BY name
SQL;
    return $query;
}}
''',
'comments':'''<?php
/** {word} metadata: @param string $text */
function {fn}(string $text): string {{
    // return class and $name remain comments
    return trim($text); /* preserve original delimiters */
}}
''',
'unicode':'''<?php
// 原始 {word} 注释 🌙
function {fn}(string $name): string {{
    return "欢迎 {{$name}} 🌌 {word}";
}}
''',
'numbers':'''<?php
const {upper}_MASK = 0xff;
function {fn}(int $value): float {{
    $scale = 1_024.5e-2;
    return ($value & {upper}_MASK) * $scale + {n};
}}
''',
'bare-snippet':'''$value = {n};
$label = '{word}';
echo $label . ': ' . $value;
''',
'callable':'''<?php
function {fn}(callable $callback, mixed $value): mixed {{
    return $callback($value, {n});
}}
''',
'first-class-callable':'''<?php
function {fn}(array $values): array {{
    $format = trim(...);
    return array_map($format, $values);
}}
''',
'object-creation':'''<?php
namespace App\\{ns};
class {cls} {{ public function __construct(public string $name) {{}} }}
function {fn}(): {cls} {{ return new {cls}('{word}'); }}
''',
'property-access':'''<?php
class {cls} {{
    public string $name = '{word}';
    public function {fn}(string $suffix): string {{ return $this->name . $suffix; }}
}}
''',
'template-heading':'''<section class="{word}">
    <h2><?= htmlspecialchars($title) ?></h2>
    <p>Original template text.</p>
</section>
''',
'template-list':'''<ul class="{word}">
<?php foreach ($items as $item): ?>
    <li><?= htmlspecialchars($item) ?></li>
<?php endforeach; ?>
</ul>
''',
'template-condition':'''<?php $active = $count > {n}; ?>
<article class="{word}">
<?php if ($active): ?>
    <strong>Ready</strong>
<?php else: ?>
    <em>Waiting</em>
<?php endif; ?>
</article>
''',
'template-block':'''<main data-kind="{word}">
<?php
$name = strtoupper($title);
echo htmlspecialchars($name);
?>
<footer>End of report.</footer>
</main>
''',
'template-script':'''<script>
const limit = {n};
console.log("{word}", limit);
</script>
<p><?php if ($enabled) {{ echo json_encode([$message, {n}]); }} ?></p>
''',
'template-style':'''<style>
.{word} {{ display: grid; gap: {n}px; }}
</style>
<div class="{word}"><?= count($values) . " / " . implode(", ", $values) ?></div>
''',
 'template-counter':"""<?php
function {fn}(array $values): int {{ return count($values) + {n}; }}
?>
<section class="{word}">
    <output><?= {fn}($items) ?></output>
    <?php for ($i = 0; $i < {n}; $i++): ?>
    <span><?= $i ?></span>
    <?php endfor; ?>
</section>
""",
 'template-choice':"""<?php
$value = match ($status) {{ 'ready' => {n}, 'empty' => 0, default => -1 }};
?>
<aside class="{word}">
    <output><?= $value ?></output>
</aside>
""",
}
WORDS='atlas cedar delta ember flora glade harbor ivory jade kernel lagoon maple nova orbit prism quartz river solar tundra umber violet willow xenon yellow zenith aurora breeze canyon dawn echo forest grove horizon iris juniper meadow north opal pine'.split()
def main():
 root=PackSpec.open('php').dataset_root/'sources/curriculum-v2';hashes={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   rng=random.Random(80329+101*index+variant);w=rng.sample(WORDS,8);source=template.format(fn=w[0]+'_format',cls=w[1].title()+'Service',base=w[2].title()+'Base',iface=w[3].title()+'View',trait=w[4].title()+'Trait',state=w[5].title()+'State',ns=w[6].title(),word=w[7],upper=w[7].upper(),n=rng.randrange(2,25),n2=rng.randrange(30,99));source=source.replace('    ',['    ','  ','\t'][variant%3])
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();target=root/family/f'{variant:02d}.php';target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve original PHP curriculum; use a new revision')
   if not target.exists():target.write_bytes(raw)
   hashes[target.relative_to(root).as_posix()]=hashlib.sha256(raw).hexdigest()
 license=root/'LICENSE'
 if not license.exists():license.write_text('Original PHP syntax/template tasks authored for Neural Semantic Highlighting.\nPrivate development dataset. No Golden, Playground or upstream copies.\n')
 lock={'format':'nsh-php-curriculum-v2','generatorSha256':file_hash(Path(__file__)),'files':hashes};p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve existing curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(hashes),'PHP tasks across',len(TEMPLATES),'families')
if __name__=='__main__':main()
