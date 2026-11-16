# Markdown neural model

Markdown/GFM source, headings, lists/tasks, tables, links/references, nested emphasis, code, opaque HTML/front matter and predicted top-level fenced regions.

```ts
const { html } = await highlighter.highlight(source, { language: "markdown" });
```

markdown, md, mdown and mkd (case normalized) share one model and canonical markdown output. Source language is explicit; content detection and MDX are not supported. Default browser registration can reuse existing code models inside predicted top-level fences; selective Markdown imports require explicit registration of desired child descriptors and otherwise retain code text.
Selective import: `@nsh/highlighter/languages/markdown`. Case-normalized IDs share one
model. Browser/Playground consumers require no language SDK, interpreter/compiler,
parser, dependency environment or Python process. Offline Gold uses Existing pinned Prettier 3.9.6 Markdown/remark/GFM parse-only assets, entities and Node, all file-hashed; no dependency or SDK installation.
Collected configurations are never executed or built.

[Evaluation](BENCHMARKS.md) separates natural, focus and visible evidence;
[known limits](KNOWN_ISSUES.md) retain measured errors and source-local scope.
Selected .pt/ONNX are inference-only. Resume full artifacts/markdown checkpoints only.
All previous data, experiments and formal models remain preserved.

The Python artifact returns base Markdown roles and predicted code regions.
The browser highlighter composes registered child models automatically; Node
consumers can use `@nsh/core/composition/markdown`. A selective Markdown descriptor
has no child dependencies: register desired languages explicitly. Unknown or
unregistered predicted bodies stay code. Nested/container code, HTML and front
matter remain opaque. Source rendering, child-model quality and base F1 are
separate scopes. This is an initial baseline with measured boundary weaknesses.
