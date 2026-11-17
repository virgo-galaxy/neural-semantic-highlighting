# Dockerfile neural model

One model highlights Dockerfile/Containerfile instructions, directives,
multistage names, ARG/ENV/LABEL, flags, paths/references, Shell/JSON forms,
continuations and heredocs. First independent real-source exact-span F1 is
**96.33% on 14 documents**.

```ts
const { html } = await highlighter.highlight(source, { language: "dockerfile" });
```

`dockerfile`, `docker` and `containerfile` (case normalized) share canonical
`dockerfile` output. Filename examples include `Dockerfile`,
`Dockerfile.production` and `build.dockerfile`; pass an explicit language.
Selective import: `@nsh/highlighter/languages/dockerfile`. It emits one model
asset and has no automatic Shell/JSON model dependencies. Existing Markdown
composition can reuse it when explicitly registered or using the default factory.

Browser and Playground need no Docker Engine, Go, Python or parser. Offline
BuildKit/Shell/JSON tools supply training supervision only. See
[evaluation](BENCHMARKS.md), [known limits](KNOWN_ISSUES.md) and
[the semantic contract](../SEMANTICS.md). Resume full artifacts checkpoints only;
exported .pt/ONNX are inference-only. All old data, models and experiments remain
preserved; the repository and packages remain private/unpublished.
