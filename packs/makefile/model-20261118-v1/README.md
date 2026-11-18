# Selected Makefile model

One standalone browser/local neural model for common GNU Make source. First
independent real-source exact-span F1 is **89.14% on 17 documents**.

```ts
const { html } = await highlighter.highlight(source, { language: "makefile" });
```

`makefile`, `make`, `mk`, `mak`, `gnumake` and `gnumakefile` are case-normalized
aliases. `Makefile`, `GNUmakefile`, `.mk` and `.mak` contents use explicit language
selection. Selective import `@nsh/highlighter/languages/makefile` emits one model;
no Make executable, source parser, Python or child Shell model runs in a browser.
Register it beside Markdown for model-predicted explicit Makefile code fences.

The model has **893,711 parameters** and 512 original UTF-8 bytes of context.
Targets, bindings, functions, directives, opaque defines and common recipe roles
share all themes/custom CSS. [Evaluation](BENCHMARKS.md),
[known limits](KNOWN_ISSUES.md) and [semantics](../SEMANTICS.md) retain the measured
scope. Resume only complete artifacts checkpoints; exported .pt/ONNX is
inference-only. Old models/data/experiments remain preserved and private.
