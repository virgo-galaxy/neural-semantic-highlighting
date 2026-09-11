# TypeScript model benchmarks

These results belong to the selected epoch **44** in `model.json`. Different epoch-specific best scores are not combined into a fictitious model score. Numbers below are rounded for reading; JSON reports retain full precision.

## 1. Checkpoint-selection validation

Source: `model.pt["validation"]`, also embedded unchanged in `reports/test-metrics.json["validation"]`.

This is training-loop validation on fixed non-overlapping windows. It is **not** the complete-document test measurement below. Training-window construction used Gold spans; document inference uses predictions, not Gold labels.

| Metric                 | Value  |
| ---------------------- | ------ |
| `boundary_macro_f1`    | 0.9929 |
| `token_type_macro_f1`  | 0.9735 |
| `modifier_f1`          | 0.9791 |
| `exact_span_precision` | 0.9883 |
| `exact_span_recall`    | 0.9959 |
| `exact_span_f1`        | 0.9921 |
| `exact_span_macro_f1`  | 0.9864 |

Predicted/Gold spans: 30506 / 30273. The validation Modifier F1 is measured at Gold BEGIN positions with sigmoid threshold 0.60 in the supplied trainer; it is not an end-to-end test-set Modifier score.

## 2. Whole-document test

Source: [test-metrics.json](reports/test-metrics.json).

| Metric              | Value  |
| ------------------- | ------ |
| Precision           | 0.9918 |
| Recall              | 0.9943 |
| Exact-span F1       | 0.9931 |
| Exact-span macro F1 | 0.9852 |
| Predicted spans     | 30451  |
| Gold spans          | 30373  |

A match requires the same document, start, end and token type. Modifiers are **not** part of this exact-match key. Macro F1 averages only token types with positive Gold support, as implemented in `evaluate.py`. The source command output reported 50 test documents; the JSON itself does not persist document count, corpus hash or split manifest. The original evaluation used MPS according to the supplied command output; that environment was not reproduced during export.

The Dataset's `fixed non-overlap` diagnostic is not the runtime inference algorithm: evaluation iterates whole documents through `predict_document_logits()` using the adaptive cursor. Decoder: `greedy`; no fixed overlap/fusion.

| Token type       | Precision | Recall | F1     | Gold support |
| ---------------- | --------- | ------ | ------ | ------------ |
| `keyword`        | 0.9965    | 0.9978 | 0.9972 | 2292         |
| `comment`        | 0.8762    | 0.9626 | 0.9173 | 294          |
| `string`         | 0.9528    | 0.9840 | 0.9682 | 1252         |
| `number`         | 1.0000    | 0.9511 | 0.9749 | 327          |
| `regexp`         | 1.0000    | 1.0000 | 1.0000 | 10           |
| `operator`       | 0.9844    | 0.9921 | 0.9882 | 1525         |
| `punctuation`    | 0.9977    | 0.9973 | 0.9975 | 15779        |
| `namespace`      | 1.0000    | 0.9286 | 0.9630 | 14           |
| `type`           | 0.9943    | 0.9951 | 0.9947 | 1223         |
| `class`          | 0.9815    | 1.0000 | 0.9907 | 106          |
| `interface`      | 1.0000    | 0.9259 | 0.9615 | 27           |
| `enum`           | 0.0000    | 0.0000 | 0.0000 | 0            |
| `enum-member`    | 0.0000    | 0.0000 | 0.0000 | 0            |
| `type-parameter` | 1.0000    | 1.0000 | 1.0000 | 69           |
| `function`       | 0.9962    | 0.9938 | 0.9950 | 801          |
| `method`         | 0.9925    | 0.9963 | 0.9944 | 1067         |
| `constructor`    | 1.0000    | 1.0000 | 1.0000 | 1            |
| `parameter`      | 0.9835    | 0.9945 | 0.9890 | 541          |
| `variable`       | 0.9900    | 0.9910 | 0.9905 | 2986         |
| `property`       | 0.9883    | 0.9906 | 0.9895 | 1711         |
| `label`          | 0.0000    | 0.0000 | 0.0000 | 0            |
| `decorator`      | 0.0000    | 0.0000 | 0.0000 | 0            |
| `tag`            | 1.0000    | 1.0000 | 1.0000 | 211          |
| `attribute`      | 0.9927    | 0.9927 | 0.9927 | 137          |

Zero support (`enum`, `enum-member`, `label`, `decorator`) means no positive test coverage, not a proven zero-accuracy capability. `regexp` has only 10 positives here; its perfect test F1 does not replace the independent challenge below.

## 3. RegExp challenge

Source: [regexp-challenge.json](reports/regexp-challenge.json).

| Metric                                             | Value        |
| -------------------------------------------------- | ------------ |
| Cases                                              | 160          |
| Precision                                          | 0.5750       |
| Recall                                             | 0.6571       |
| Exact RegExp F1                                    | 0.6133       |
| TP / FP / FN                                       | 69 / 51 / 36 |
| Positive cases with an exactly matching RegExp set | 54/100       |
| Negative cases without RegExp false positives      | 59/60        |
| All cases with an exactly matching RegExp set      | 113/160      |

Case-level correctness concerns the **RegExp span set**, not all semantic labels in the source. An off-by-one span can count as both one FP and one FN.

| Category                   | Cases | TP  | FP  | FN  | F1     | Exact cases |
| -------------------------- | ----- | --- | --- | --- | ------ | ----------- |
| `negative/comment`         | 10    | 0   | 0   | 0   | 0.0000 | 10/10       |
| `negative/division`        | 25    | 0   | 0   | 0   | 0.0000 | 25/25       |
| `negative/jsx-slash`       | 10    | 0   | 0   | 0   | 0.0000 | 10/10       |
| `negative/string-template` | 15    | 0   | 2   | 0   | 0.0000 | 14/15       |
| `positive/basic`           | 15    | 13  | 6   | 2   | 0.7647 | 11/15       |
| `positive/context`         | 25    | 22  | 3   | 6   | 0.8302 | 17/25       |
| `positive/escape-class`    | 20    | 9   | 18  | 11  | 0.3830 | 5/20        |
| `positive/group-assertion` | 20    | 7   | 20  | 13  | 0.2979 | 5/20        |
| `positive/typescript-tsx`  | 20    | 18  | 2   | 4   | 0.8571 | 16/20       |

For negative-only categories, inspect clean/exact-case counts; a printed F1 of zero with no positive Gold spans does not mean those cases failed.

## 4. Paired contextual RegExp challenge

Source: [regexp-paired-challenge.json](reports/regexp-paired-challenge.json).

| Condition  | F1     | Exact cases |
| ---------- | ------ | ----------- |
| Isolated   | 0.6882 | 30/40       |
| Contextual | 0.7333 | 33/40       |

Transitions: both correct 27; rescued by context 6; hurt by context 3; neither correct 4. Net exact-rate delta: +7.50 percentage points. All supplied pair inputs fit within 512 bytes; this does not compare different context sizes or prove a larger model is needed.

## 5. String interior-boundary diagnostic

Source: [string-fragmentation-test.json](reports/string-fragmentation-test.json).

| Metric                                   | Value     |
| ---------------------------------------- | --------- |
| Gold string interior character positions | 26034     |
| Positions predicted other than I         | 251       |
| Rate                                     | 0.9641%   |
| B winners / O winners                    | 100 / 151 |

The denominator is character positions **inside Gold strings**, not strings, windows or documents. This is a boundary-head diagnostic, not rendered-visual error rate or exact-span F1. The report includes the first 20 examples after confidence sorting, not all mistakes and not a representative random sample.

## 6. JSX / TSX challenge

Source: [jsx-tsx-challenge.json](reports/jsx-tsx-challenge.json).

This challenge targets JSX/TSX-specific semantic boundaries and ambiguity cases rather than general React framework semantics. It covers tags, attributes, JSX text cleanliness, embedded expressions, fragments, qualified tags, spread props, realistic TSX, TypeScript types inside TSX, and generic-vs-JSX ambiguity.

| Metric                     | Value       |
| -------------------------- | ----------- |
| Cases                      | 50          |
| Assertions                 | 162         |
| Exact assertions           | 162/162     |
| Assertion accuracy         | 100.00%     |
| Semantic exact assertions  | 156/156     |
| JSX text clean assertions  | 6/6         |
| Exact cases                | 50/50       |
| Tag/attribute precision    | 0.9934      |
| Tag/attribute recall       | 1.0000      |
| Tag/attribute F1           | 0.9967      |
| Tag/attribute TP / FP / FN | 151 / 1 / 0 |

### Focus token types

| Token type  | Precision | Recall | F1     | TP  | FP  | FN  |
| ----------- | --------- | ------ | ------ | --- | --- | --- |
| `attribute` | 1.0000    | 1.0000 | 1.0000 | 40  | 0   | 0   |
| `tag`       | 0.9911    | 1.0000 | 0.9955 | 111 | 1   | 0   |

### Document kinds

| Document kind | Assertions | Exact cases |
| ------------- | ---------- | ----------- |
| `jsx`         | 99/99      | 32/32       |
| `tsx`         | 63/63      | 18/18       |

### Categories

| Category                | Assertions |
| ----------------------- | ---------- |
| `jsx/attributes`        | 18/18      |
| `jsx/basic-tags`        | 18/18      |
| `jsx/expressions`       | 24/24      |
| `jsx/fragments-text`    | 13/13      |
| `jsx/qualified-tags`    | 19/19      |
| `jsx/spread-props`      | 7/7        |
| `tsx/generic-ambiguity` | 14/14      |
| `tsx/realistic`         | 36/36      |
| `tsx/types`             | 13/13      |

The only focus false positive in this run was `const` predicted as `tag` in `jsx-attr-005`. All explicitly asserted semantics were correct, including all JSX text-clean checks and all TSX generic-ambiguity assertions. This challenge does **not** claim React-aware or Tailwind-aware semantics; React and Tailwind examples are still highlighted through the underlying JavaScript/TypeScript/JSX/TSX semantic model.

## Reproduction commands

Run from the repository root with the original Dataset installed separately. Write new evaluation results to `artifacts/`, not over the immutable reports in this directory:

```bash
mkdir -p artifacts/typescript/model-verification
.venv/bin/python training/typescript/evaluate.py \
  --checkpoint packs/typescript/model/model.pt --split test --decoder greedy \
  --output artifacts/typescript/model-verification/test-metrics.json
.venv/bin/python training/typescript/regexp_challenge.py \
  --checkpoint packs/typescript/model/model.pt --max-errors 40 \
  --output artifacts/typescript/model-verification/regexp-challenge.json
.venv/bin/python training/typescript/regexp_paired_challenge.py \
  --checkpoint selected=packs/typescript/model/model.pt \
  --output artifacts/typescript/model-verification/regexp-paired-challenge.json
.venv/bin/python training/typescript/fragmentation.py \
  --checkpoint packs/typescript/model/model.pt --split test --token-type string --max-examples 20 \
  --output artifacts/typescript/model-verification/string-fragmentation-test.json
.venv/bin/python training/typescript/jsx_tsx_challenge.py \
  --checkpoint packs/typescript/model/model.pt \
  --output artifacts/typescript/model-verification/jsx-tsx-challenge.json
```

`NSH_DATASET_ROOT` selects the external Dataset root in the supplied code. The challenge inputs and corpus are not included in the review bundle; exact reproduction also needs their original versions. No inference latency, throughput, memory, browser runtime or all-language coverage benchmark was supplied. CPU export checks do not fill those gaps. No new/old champion comparison is claimed without the same test set, decoder and windowing configuration.
