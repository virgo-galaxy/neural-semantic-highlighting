# Diff/Patch neural model

One standalone model highlights original unified/Git patch lines. First natural
independent exact-span F1 is **98.03% on 26 files**.

```ts
const { html } = await highlighter.highlight(source, { language: "patch" });
```

`diff`, `patch`, `udiff`, `unified-diff` and `git-diff` share canonical `diff`
output. `.diff` and `.patch` are source suffixes; pass an explicit language.
Selective `@nsh/highlighter/languages/diff` and `languages/patch` exports share
one model/asset. Markdown can reuse a registered diff/patch fence.
No Git, Python, SDK, source parser or patch-application service is needed.

All three themes supply light/dark addition/deletion colors, customizable with
`--nsh-addition` and `--nsh-deletion`. Original plus/minus signs remain visible.
Body code stays opaque Diff content; it is not dispatched to a programming model.
See [evaluation](BENCHMARKS.md), [limits](KNOWN_ISSUES.md) and
[semantics](../SEMANTICS.md). Full artifacts checkpoints are the training sources;
formal .pt/ONNX are inference only. All previous data/weights/experiments remain
preserved; repo and packages remain private/unpublished.
