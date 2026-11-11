# Selected CSS family model

One small neural model highlights CSS, SCSS and Less source through the shared
UTF-16 semantic-span contract. It is a usable initial baseline with explicit
[known issues](KNOWN_ISSUES.md), rather than a syntax validator or Sass/Less compiler.

| Property          | Value                                                                 |
| ----------------- | --------------------------------------------------------------------- |
| Selected epoch    | 8                                                                     |
| Parameters        | 894,227                                                               |
| Input             | UTF-8 bytes, vocabulary 257 including padding                         |
| Context           | 512 bytes                                                             |
| Transformer       | 4 layers, width 128, 4 heads, FFN 512                                 |
| Heads             | BIO 3, semantic types 15, declaration modifier 1                      |
| Position encoding | Learned absolute positions                                            |
| Runtime           | Pure-neural predicted adaptive cursor, greedy mean-logit span decoder |
| Public offsets    | UTF-16, `[start,end)`                                                 |
| Training device   | MPS, Python 3.12.2, PyTorch 2.14.0                                    |

`model.pt` is an inference-only float32 export. `model.json` binds its hash,
ordered labels, source checkpoint, dataset identity, decoder and reports.
Keep this bundle together. No parser, scanner, language server, Sass compiler,
Less execution or external symbol resolution participates in runtime inference.

## Evidence

The frozen candidate's first held-out, whole-document adaptive test reports:

| Document kind | Documents | Gold spans | Exact-span F1 | Macro F1 | With modifiers F1 |
| ------------- | --------: | ---------: | ------------: | -------: | ----------------: |
| CSS           |         5 |      1,091 |        99.04% |   97.02% |            98.76% |
| SCSS          |        28 |     12,108 |        99.40% |   91.72% |            99.29% |
| Less          |        26 |      9,001 |        99.42% |   90.06% |            99.30% |

These counts are small, especially CSS. Missing or rare semantic roles limit
what the aggregate scores establish. The development probes deliberately expose
remaining failures, including one wrong role for `auto-fit` in the Surface layout.
Read [BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md) before
interpreting these numbers as universal syntax coverage.

## Training lineage

The selected run is `artifacts/css/context512-modern-grid-20261108-01`.
It initializes compatible backbone/BIO weights from the full Go epoch-29 training
checkpoint `artifacts/go/context512-20260913-074648-569634/best.pt`, with shared
head rows matched by semantic label name. CSS-only roles start fresh. The Go
checkpoint is read-only; CSS uses a fresh optimizer, RNG and selection state.
This is weights-only initialization, not resuming Go training or importing its
inference artifact. The existing selected Go and TypeScript bundles are preserved.

The run completes eight epochs, 1,032 optimizer steps, in about 4 minutes 44 seconds
including training, validation and checkpoint saves. It uses batch 32, AdamW
0.0003, weight decay 0.01, gradient clipping 1.0, modifier loss weight 0.1,
modifier threshold 0.60, seed 42 and kind-balanced window presentations.
Selection is the mean per-kind fixed-window validation exact-span macro F1;
the selected score is 0.8829993120. The actual adaptive runtime is evaluated
separately. Held-out test was run only after candidate selection.

Resumable checkpoints, optimizer/RNG state and all prior experiments remain in
`artifacts/css`. Continue from that run's `last.pt`; never resume from this
inference artifact. Dataset source and prepared tensors remain outside Git under
`~/Datasets/neural-semantic-highlighting/css`.

## Use

Start the Playground with `pnpm dev`. CSS, SCSS and Less share one selected ONNX
model, loaded on demand in the browser Worker; no Python provider is required.
Frontend applications use `@nsh/highlighter` with `css`, `scss` or `less`; see the
[consumer integration](../../../README.md#highlight-code) and
[browser verification](../../../docs/browser-runtime.md).

The Python CLI remains a native development/reference tool. Pass
`--checkpoint path/to/candidate.pt` to inspect compatible development weights;
this does not select the Playground's browser model.

```bash
.venv/bin/python -m packs.css.runtime.local --text '.card { color: red; }' --document-kind css
.venv/bin/python -m packs.css.runtime.local --stdio
```
