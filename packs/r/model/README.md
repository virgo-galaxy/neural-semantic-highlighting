# R neural model

Original .R/.r/.Rprofile source; common statistical/data, native and magrittr pipe syntax.

```ts
const { html } = await highlighter.highlight(source, { language: "r" });
```

Selective import: `@nsh/highlighter/languages/r`. Case-normalized IDs share one
model. Browser/Playground consumers require no language SDK, interpreter/compiler,
parser, dependency environment or Python process. Offline Gold uses r-lib tree-sitter-r 1.3.0 and Tree-sitter 0.25.10, compiled with existing Clang only in project cache.
Collected projects and dependencies never execute or typecheck.

[Evaluation](BENCHMARKS.md) separates natural, focus and visible evidence;
[known limits](KNOWN_ISSUES.md) retain measured errors and source-local scope.
Selected .pt/ONNX are inference-only. Resume full artifacts/r checkpoints only.
All previous data, experiments and formal models remain preserved.
