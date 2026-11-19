# PHP neural model

Original `.php`, `.phtml` and tagless PHP snippets: functions, classes/interfaces/
traits/enums, properties, typed/promoted parameters, arrays, closures, attributes,
named arguments, match/nullsafe syntax, interpolated strings, heredoc and nowdoc.
Targets common accepted modern PHP 8 syntax, without a claim of every newest
feature or framework DSL. DocBlocks remain opaque comments.

```js
const { html } = await highlighter.highlight(source, { language: "php" });
```

Selective `@nsh/highlighter/languages/php` also registers existing HTML/JS/CSS
models for neural-region composition. It never executes PHP, scans tags at runtime
or starts a Python/PHP/server process. No interpreter, SDK, Composer or installed
project dependencies are required. Base-only local reference:
`.venv/bin/python -m packs.php.runtime.local --file example.php`.

[Evidence](BENCHMARKS.md) distinguishes base PHP/region accuracy from composed
visible template results. [Known issues](KNOWN_ISSUES.md) retain measured limits.
Selected `.pt` is inference-only; full checkpoints stay under `artifacts/php`.
All previous language data, experiments and models remain preserved.
