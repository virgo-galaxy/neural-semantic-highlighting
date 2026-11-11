# Scala neural model

Common Scala 2/3 .scala/.sc/.sbt source, significant indentation, givens/using, extensions, enums, generics and interpolated strings.

```ts
const { html } = await highlighter.highlight(source, { language: "scala" });
```

Selective import: `@nsh/highlighter/languages/scala`. Case-normalized IDs share one
model. Browser/Playground consumers require no language SDK, interpreter/compiler,
parser, dependency environment or Python process. Offline Gold uses Tree-sitter Scala 0.26.12 with runtime 0.25.10, compiled with existing Clang only in project cache.
Collected projects and dependencies never execute or typecheck.

[Evaluation](BENCHMARKS.md) separates natural, focus and visible evidence;
[known limits](KNOWN_ISSUES.md) retain measured errors and source-local scope.
Selected .pt/ONNX are inference-only. Resume full artifacts/scala checkpoints only.
All previous data, experiments and formal models remain preserved.
