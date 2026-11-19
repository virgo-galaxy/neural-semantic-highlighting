# TypeScript model

This directory contains the currently selected TypeScript-family **inference artifact**, its identity record, and the supplied evaluation reports. It is not a training-run directory or a release of a standalone browser runtime.

## Selected artifact

| Field                     | Value                                                               |
| ------------------------- | ------------------------------------------------------------------- |
| Selected checkpoint epoch | 44                                                                  |
| Selection metric          | validation `exact_span_macro_f1`                                    |
| Selection score           | 0.9864448243                                                        |
| Parameters                | 897,065                                                             |
| Context                   | 512 UTF-8 bytes, not BPE tokens                                     |
| Input vocabulary          | 256 byte values + PAD 256                                           |
| Architecture              | Transformer encoder; 4 layers, 128 dimensions, 4 heads, FFN 512     |
| Position encoding         | learned absolute positions                                          |
| Output heads              | 3 BIO classes; 24 token types; 14 modifiers                         |
| Numeric weights           | float32; no quantization or retraining during export                |
| Public span offsets       | UTF-16 code units, start inclusive / end exclusive                  |
| Document inference        | predicted adaptive cursor, greedy decoding, modifier threshold 0.60 |

`model.pt` retains the current loader fields: `format`, `epoch`, `model_state_dict`, `config`, `schema`, and `validation`. Optimizer state and resume bookkeeping are omitted. `model.json` records hashes, ordered labels, decoder settings and provenance. Keep this pair together. Do **not** pass this inference artifact to `train.py --resume`; keep the original training checkpoints in `artifacts/` for that purpose.

## Scope

The pack labels the local semantic role of each span as specified in [SEMANTICS.md](../SEMANTICS.md). References do not have to preserve their declaration-kind identity. Cross-file resolution, navigation, business-logic understanding and theme colors are not model outputs.

The following document kinds are declared in the pack manifest. This list is a capability declaration, not evidence of equal measured quality for every extension.

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

Frontend applications and Playground use the selected ONNX weights in the browser
Worker through `@nsh/highlighter`, including JS/TS/JSX/TSX. No Python provider is
required; see [consumer integration](../../../README.md#highlight-code) and
[browser verification](../../../docs/browser-runtime.md).

For native development/reference output, use the existing Python loader from the
repository root:

```bash
.venv/bin/python training/typescript/predict.py \
  --checkpoint packs/typescript/model/model.pt \
  --text 'const value = 1;'
```

The CLI prints native diagnostic text. It needs the existing Python runtime code
and PyTorch, but not the training dataset to infer a supplied string. A `.pt` file
is not directly executable by the JS library: browser consumers load the reviewed
ONNX export under `../browser/`. The later browser integration does not change the
selected weights, original experiment defaults or historical evaluation evidence.

## Contents and maintenance

- [BENCHMARKS.md](BENCHMARKS.md): metric definitions, measured results, and reproduction commands.
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md): observed limitations and proposed follow-up checks, not promises of solved problems.
- `reports/`: the four supplied JSON reports, copied byte-for-byte without rewriting their experiment paths.
- `model.json`: identity, hashes, source-file fingerprints and explicitly missing provenance.
- `EXPORT_CHECKS.json`: export integrity, current-loader and CPU sample-equivalence checks.

Keep the generated JSON files byte-for-byte intact. Exclude `packs/typescript/model/**/*.json` from formatting in the repository `.prettierignore` (not `.gitignore`). Markdown documentation can be formatted normally.

Export integrity and CPU sample-equivalence results are recorded in `EXPORT_CHECKS.json`.

Only this selected artifact belongs here. Keep historical checkpoints in their existing experiment directories; keep `challenges/`, `dataset/`, `fixtures/`, `labeling/`, the manifest, the schema and the semantic contract. A later selected model should update weights, identity, reports and documentation together in a reviewed Git change.

## Evidence and provenance limits

The test JSON's embedded validation block matches the supplied checkpoint. The other reports identify the same experiment path and inference configuration, but do not contain a checkpoint hash or epoch. Their association is based on the supplied bundle and maintainer's evaluation run, not a retroactive cryptographic proof. The hashes added now identify the delivered files; they are not signatures.

No frozen corpus manifest, corpus/split hash, original training commit, or training environment lock was supplied. Source hashes identify the code available at export, which is not asserted to be the exact code of every historical epoch. `exportRepositoryCommit`, when available, identifies the local repository at export, not the original training commit. Full-dataset scores were imported, not rerun by the exporter.

No license or complete training-source license inventory was supplied in the review bundle. This directory does not invent a license grant for weights or upstream code snippets; complete that review before public distribution. Public model claims must disclose the RegExp weaknesses and coverage gaps below, rather than advertise universal 99% accuracy.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
