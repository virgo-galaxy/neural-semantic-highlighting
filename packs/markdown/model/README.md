# Markdown neural model

Markdown/GFM source highlighting, with explicit registered child models for
predicted top-level fenced code. The November 17 optimization reaches **95.10%
exact-span F1 on 20 new independent real documents**. The unchanged 14-file v1
regression improves from 77.24% to 95.99%.

```ts
const { html } = await highlighter.highlight(source, { language: "markdown" });
```

Aliases `md`, `mdown`, `mkd` share this model. Selective import:
`@nsh/highlighter/languages/markdown`. Browser/Playground use no Python or parser.
The same 894,227-parameter, 512-byte Transformer now uses a train-fitted joint
BIO/role decoder. Its probabilities and all neural outputs are shared by browser
and Python; source spelling never repairs predictions.

[Evaluation](BENCHMARKS.md) separates independent test, exposed regression,
authored curriculum and visible probes. [Known limits](KNOWN_ISSUES.md) include
remaining embedded-code and edge-case errors. The complete prior native bundle
remains in [model-20261116-v1](../model-20261116-v1/README.md), with its paired
[browser bundle](../browser-20261116-v1/model.json). Existing data and full
artifacts checkpoints remain untouched. Resume full training checkpoints only.
