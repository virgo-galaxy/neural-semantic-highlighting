# Selected Vue model

An initial Vue SFC baseline covering Vue 2, Vue 3 Options/Composition API and
Vue 3.2 script setup, through one `vue` document kind. Version-specific syntax
is deliberately included; Vue 2 filters, old slots, `.sync` and `.native` are not
discarded merely because Vue 3 removed them. This is source highlighting, not
framework execution or compiler-version validation.

| Property         | Value                                                                   |
| ---------------- | ----------------------------------------------------------------------- |
| Selected epoch   | 35                                                                      |
| Parameters       | 894,485                                                                 |
| Transformer      | 4 layers, width 128, 4 heads, FFN 512                                   |
| Input / context  | UTF-8 bytes, vocabulary 257 including padding, 512 bytes                |
| Heads            | BIO 3, markup/region types 17, closing modifier 1                       |
| Positions        | Learned absolute embeddings                                             |
| Public offsets   | Original UTF-16 `[start,end)`                                           |
| Decoder          | Predicted adaptive cursor, greedy mean logits, adjacent body coalescing |
| Training backend | MPS, Python 3.12.2, PyTorch 2.14.0                                      |

The Vue model recognizes markup, directives as attribute names, interpolation
interiors and embedded language regions. The shared JS/TS/JSX/TSX and CSS/SCSS/Less
models supply code-body semantics. Mustache interiors use a fixed expression
wrapper and project results back to original positions. Attribute values, including
directive expressions and Tailwind classes, remain whole strings in this first
contract. No Vue/HTML parser, source regex detector or source execution participates
in runtime region selection. See [SEMANTICS.md](../SEMANTICS.md).

## Evidence

The frozen candidate's first real-source held-out test:

| Source profile     | Documents | Base F1 | Composed F1 | Composed with modifiers F1 |
| ------------------ | --------: | ------: | ----------: | -------------------------: |
| Vue 2              |         5 |  97.48% |      96.37% |                     96.20% |
| Vue 3              |         4 |  97.80% |      97.86% |                     97.71% |
| Vue 3.2            |         1 |  97.67% |      96.18% |                     96.18% |
| All natural source |        10 |  97.63% |      97.12% |             See raw report |

Base and composed scopes use different span vocabularies; their scores are not an
improvement comparison. Base test has 630 Gold spans; composed has 1,291. No
document is excluded from final composed validation/test. Real validation has
only seven documents, including one Vue 3.2 component: composed F1 is 97.12%.
These are small samples, especially Vue 3.2, not universal framework guarantees.

The independent template-family focus holdout has 96 test documents: base F1
95.18%, composed F1 97.01%. These original grammar variants are not independent
real-source observations. Six of nine visible Golden development cases are fully
exact; remaining cases expose dual-script TSX, Less/custom-block boundaries and
opaque preprocessor limits. Typed region test F1 is 67.86%, distinct from composed
code accuracy. Read [BENCHMARKS.md](BENCHMARKS.md), [KNOWN_ISSUES.md](KNOWN_ISSUES.md)
and the retained raw mismatches.

## Reuse and training lineage

Selected run: `artifacts/vue/context512-compact-20261108-01`, initialized
weights-only from the complete HTML epoch-20 checkpoint
`artifacts/html/context512-fragments-20261108-01/best.pt`. Shared backbone/BIO,
matching semantic rows and closing modifier are copied; six new region rows start
fresh. Optimizer, RNG, loss weights and selection history are Vue-owned and fresh.
The selected HTML inference artifact is not a continuation checkpoint.

The Transformer, adaptive inference, UTF-16 decoding, masked loss and atomic-file
primitives reuse the HTML implementation without modifying it. Runtime composition
reuses the existing child weights/processes. Code hashes bind both shared and
Vue-owned files. Existing TypeScript, Go, CSS and HTML formal models are preserved.

This run completed 36 epochs / 432 optimizer steps in about 2 minutes 6 seconds,
including validation and checkpoint saves. Selected epoch 35 scores 0.8091739239
on the mean per-profile natural fixed-window validation exact-span macro F1.
Actual adaptive/composed evaluation is separate. AdamW 0.0003, natural batch 32,
bounded focus batch 32 after each natural batch, decay 0.01, clipping 1.0, modifier
loss 0.1 / threshold 0.60, seed 42, patience ten. Each epoch presents 168 natural
windows once and 192 rotating focus presentations; repetition is not new data.

Earlier curriculum versions and the first 25-epoch experiment remain preserved.
All overlapping source-family holdouts are frozen across revisions. This candidate
starts again from the full HTML checkpoint, rather than inheriting an earlier Vue
optimizer or data history. Only this frozen candidate was evaluated on final test.

## Use

`pnpm dev` exposes one Vue entry with versioned and mixed-style examples. Vue,
TypeScript-family and CSS-family local processes load lazily and are reused.
`NSH_VUE_CHECKPOINT` optionally selects an experimental checkpoint at startup.
Browser-native inference is not implemented.

```bash
.venv/bin/python -m packs.vue.runtime.local --text '<template><p>{{ title }}</p></template>'
.venv/bin/python -m packs.vue.runtime.local --stdio
```

The Python CLI returns base markup/region roles. Use the composite `SemanticPack`
for child-language semantics, as Playground does. `model.pt` is an inference-only
float32 export, with no optimizer/RNG state. `model.json` binds its hash, ordered
labels, source checkpoint, data, code and reports. Resume only the original run's
full `last.pt`, with source data under `~/Datasets/neural-semantic-highlighting/vue`.
