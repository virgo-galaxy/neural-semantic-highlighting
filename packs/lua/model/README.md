# Lua neural model

Common Lua 5.x .lua functions, closures, tables, methods, long strings/comments, 5.4 attributes and 5.5 global declarations/named varargs.

```ts
const { html } = await highlighter.highlight(source, { language: "lua" });
```

Selective import: `@nsh/highlighter/languages/lua`. Case-normalized IDs share one
model. Browser/Playground consumers require no language SDK, interpreter/compiler,
parser, dependency environment or Python process. Offline Gold uses Tree-sitter Lua 0.5.0 at 10fe0054 with runtime 0.25.10, compiled with existing Clang only in project cache.
Collected projects and dependencies never execute or typecheck.

[Evaluation](BENCHMARKS.md) separates natural, focus and visible evidence;
[known limits](KNOWN_ISSUES.md) retain measured errors and source-local scope.
Selected .pt/ONNX are inference-only. Resume full artifacts/lua checkpoints only.
All previous data, experiments and formal models remain preserved.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
