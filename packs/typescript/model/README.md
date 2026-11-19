# JavaScript / TypeScript neural model

Use the browser highlighter for JS/TS/JSX/TSX, including React component source:

```ts
const { html } = await highlighter.highlight(source, { language: "tsx" });
```

Frontend applications and Playground run the selected ONNX weights in a browser
Worker. No Python provider, compiler or parser is required by consumers. See
[consumer integration](../../../README.md#highlight-code).

## Selected artifact

| Field                 | Value                                                                                         |
| --------------------- | --------------------------------------------------------------------------------------------- |
| Full-checkpoint epoch | 58                                                                                            |
| Parameters            | 897,833                                                                                       |
| Architecture          | Four layers, width 128, four heads, FFN 512, learned five-byte depthwise residual             |
| Context / vocabulary  | 512 original UTF-8 bytes; 256 byte values plus PAD 256                                        |
| Position encoding     | Learned absolute positions                                                                    |
| Heads                 | Three BIO classes, 24 semantic roles, 14 modifiers                                            |
| Runtime               | Predicted adaptive cursor; greedy decoding; modifier threshold 0.60                           |
| Numeric weights       | Float32; no export quantization or retraining                                                 |
| Output                | Original UTF-16 code units, start inclusive / end exclusive                                   |
| Selection             | Minimum natural-validation and authored RegExp-validation F1, with natural micro/macro guards |
| Selection score       | 0.9893992933                                                                                  |

Natural legacy regression F1 is **99.45%** on 50 files. The 24 read-only real
Virgo Design TSX files reach **99.39%**. RegExp development F1 is **93.27%**,
with **96.48%** on the separate first-read authored RegExp holdout. These scopes
remain separate; negative slash precision and long-content limitations remain in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Document kinds

| Document kind                     | Extensions |
| --------------------------------- | ---------- |
| `javascript`                      | `.js`      |
| `javascript-esm`                  | `.mjs`     |
| `javascript-commonjs`             | `.cjs`     |
| `jsx`                             | `.jsx`     |
| `typescript`                      | `.ts`      |
| `typescript-esm`                  | `.mts`     |
| `typescript-commonjs`             | `.cts`     |
| `tsx`                             | `.tsx`     |
| `typescript-declaration`          | `.d.ts`    |
| `typescript-esm-declaration`      | `.d.mts`   |
| `typescript-commonjs-declaration` | `.d.cts`   |

## Artifacts and native development

`model.pt` is inference-only: format, epoch, state tensors, configuration, schema
and validation, without optimizer/RNG/resume state. `model.json` binds weights,
ordered labels, source checkpoint, refinement data and report hashes. Never resume
training from this inference artifact. Full experiments remain under
`artifacts/typescript`; the bounded refinement recipe is in
[the quality log](../../../docs/quality-optimization.md#jsts-refinement-recipe).

For an optional native reference, with the existing Python/PyTorch environment:

```sh
.venv/bin/python training/typescript/predict.py \
  --checkpoint packs/typescript/model/model.pt \
  --text 'const value = 1;'
```

`reports/` separates corpus cohorts, RegExp/paired challenges, JSX/TSX assertions
and copy audits. Per-file diagnostics are compacted with the full immutable
experiment-report hash; aggregate metrics are unchanged. Numerical ONNX export
checks live in `../browser/verification.json`.

The [previous complete bundle](../model-20261119-v1/README.md) preserves its
original reports, export checks and historical provenance limits. New refinement
hashes do not retroactively prove every old training epoch. Original datasets,
full checkpoints and preceding inference artifacts remain intact and private.
Local semantic-role scope is defined in [SEMANTICS.md](../SEMANTICS.md); cross-file
resolution and theme colors are not model outputs.
