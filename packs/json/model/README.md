# JSON / JSONC neural model

Strict JSON and comment-enabled JSONC with optional trailing commas, original quoted keys/values, decimal numbers, keywords, nested objects/arrays and opaque string content.

```ts
const { html } = await highlighter.highlight(source, { language: "json" });
```

JSON and JSONC remain distinct document kinds with separate evaluations; `languages/jsonc` re-exports `languages/json`, sharing one model asset. Named .json configuration files with comments require explicit `jsonc`.
Selective import: `@nsh/highlighter/languages/json`. Case-normalized IDs share one
model. Browser/Playground consumers require no language SDK, interpreter/compiler,
parser, dependency environment or Python process. Offline Gold uses Pinned Microsoft jsonc-parser 3.3.1 official npm assets with SHA-512/archive/per-file hashes, using existing Node only in project cache.
Collected projects and dependencies never execute or typecheck.

[Evaluation](BENCHMARKS.md) separates natural, focus and visible evidence;
[known limits](KNOWN_ISSUES.md) retain measured errors and source-local scope.
Selected .pt/ONNX are inference-only. Resume full artifacts/json checkpoints only.
All previous data, experiments and formal models remain preserved.
