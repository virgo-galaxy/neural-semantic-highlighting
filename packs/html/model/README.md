# Selected HTML model

An initial modern HTML baseline for documents and fragments. It follows the
WHATWG HTML Living Standard, including custom elements and foreign content;
explicitly obsolete features are not training targets. Ordinary markup is usable,
with material [limits](KNOWN_ISSUES.md) in raw-text contexts and body boundaries.

| Property         | Value                                                                   |
| ---------------- | ----------------------------------------------------------------------- |
| Selected epoch   | 20                                                                      |
| Parameters       | 893,711                                                                 |
| Transformer      | 4 layers, width 128, 4 heads, FFN 512                                   |
| Input/context    | UTF-8 bytes, vocabulary 257 including padding, 512 bytes                |
| Heads            | BIO 3, semantic types 11, closing-tag modifier 1                        |
| Positions        | Learned absolute embeddings                                             |
| Decoder          | Predicted adaptive cursor, greedy mean logits, adjacent body coalescing |
| Public offsets   | UTF-16 `[start,end)`                                                    |
| Training backend | MPS, Python 3.12.2, PyTorch 2.14.0                                      |

`model.pt` contains float32 inference weights. `model.json` binds its identity,
labels, source checkpoint, immutable data and evidence. The base model predicts
markup and JavaScript/CSS/data body regions. `runtime/composite.ts` invokes the
existing JavaScript and CSS neural packs only inside predicted regions, restoring
original offsets. The public schema is their superset, not a larger HTML head.
No parser, source scanner, regex region detector or source execution participates
in runtime inference. Attribute snippets remain strings, including Tailwind.

## Evidence

The frozen candidate's first held-out adaptive test is reported separately for
collected source (`natural`) and original grammar curriculum (`focus`):

| Scope/stream                    | Documents | Gold spans | Exact-span F1 | Macro F1 | With modifiers F1 |
| ------------------------------- | --------: | ---------: | ------------: | -------: | ----------------: |
| Base HTML, natural              |        10 |      1,423 |        96.37% |   75.75% |            96.37% |
| Composed HTML + JS/CSS, natural |         9 |      1,505 |        96.53% |   90.04% |            95.94% |
| Base HTML, focus                |        48 |      1,984 |        89.86% |   75.76% |            89.86% |
| Composed HTML + JS/CSS, focus   |        48 |      2,416 |        89.18% |   69.35% |            89.18% |

One real test document has incomplete existing JS reference Gold and is explicitly
excluded from composed scoring, while remaining in base evaluation. These scopes
have different documents and span vocabularies, so their F1 values are not an
improvement comparison. Exact whole-body test F1 is only 45.45%: small region
boundary errors and extra fragments matter even when most characters are correct.
Only four of ten visible Golden development cases are entirely exact. See
[BENCHMARKS.md](BENCHMARKS.md) and the archived raw reports before interpreting
aggregate results as general mixed-language coverage.

## Training and use

Selected run: `artifacts/html/context512-fragments-20261108-01`, initialized
weights-only from full CSS epoch-8 checkpoint
`artifacts/css/context512-modern-grid-20261108-01/best.pt`. Shared backbone/BIO
and semantic head rows are copied by name; HTML roles and closing modifier start
fresh. Optimizer, RNG, sampling and selection history start fresh. The existing
CSS, Go and TypeScript formal artifacts remain unchanged.

The run completed 25 epochs / 600 optimizer steps in about 2 minutes 10 seconds,
including validation and checkpoint saves; early stopping retained epoch 20.
AdamW 0.0003, batch 32, weight decay 0.01, clipping 1.0, modifier loss 0.1,
threshold 0.60, seed 42, patience five. Every epoch presents 358 natural windows
once plus 192 bounded curriculum presentations. Selection within the run uses
natural fixed-window validation exact-span macro F1 (0.7925265539).

An optional 512-parameter local-context experiment improved some comment scores
but lowered composed validation F1 (97.62% versus 97.93%); it was not selected.
A train-only transition-decoder diagnostic was also not adopted. Neither changes
this inference bundle. Earlier experiments, curriculum versions and checkpoints
remain preserved; none of those candidates was tested on the final test split.

Start the Playground with `pnpm dev` and select HTML. The HTML descriptor loads
its selected ONNX model and JS/TS/CSS dependencies on demand in the browser Worker.
Frontend applications use `{ language: "html" }`; no Python process is required.
See the [consumer integration](../../../README.md#highlight-code) and
[browser verification](../../../docs/browser-runtime.md).

The Python CLI below remains a native development/reference tool. Its
`--checkpoint path/to/candidate.pt` option selects compatible development weights,
without changing the Playground's browser model.

```bash
.venv/bin/python -m packs.html.runtime.local --text '<p>Hello</p>'
.venv/bin/python -m packs.html.runtime.local --stdio
```

The Python CLI returns base markup/body roles. Use the composite `SemanticPack`
for embedded JS/CSS semantics, as the Playground does. Resume training only from
the original run's full `last.pt` under `artifacts`, never this inference artifact.
Data remains under `~/Datasets/neural-semantic-highlighting/html`, outside Git.
