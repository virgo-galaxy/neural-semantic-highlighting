# INI neural model

INI .ini/.cfg and EditorConfig source, sections/root options, =/: key-value delimiters, full-line comments, duplicates, empty/valueless options and indented continuations.

```ts
const { html } = await highlighter.highlight(source, { language: "ini" });
```

ini, cfg and editorconfig (case normalized) use one INI descriptor and canonical ini output. .ini/.cfg and .editorconfig share it; generic .conf requires explicit INI selection.
Selective import: `@nsh/highlighter/languages/ini`. Case-normalized IDs share one
model. Browser/Playground consumers require no language SDK, interpreter/compiler,
parser, dependency environment or Python process. Offline Gold uses Existing CPython 3.12 ConfigParser with interpolation disabled, independent section/key inventory validation and Python/stdlib/teacher SHA-256 provenance; no downloaded tool or SDK.
Collected configurations are never executed or built.

[Evaluation](BENCHMARKS.md) separates natural, focus and visible evidence;
[known limits](KNOWN_ISSUES.md) retain measured errors and source-local scope.
Selected .pt/ONNX are inference-only. Resume full artifacts/ini checkpoints only.
All previous data, experiments and formal models remain preserved.
