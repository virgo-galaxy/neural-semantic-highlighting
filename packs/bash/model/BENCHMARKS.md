# bash quality evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match;
modifier scores remain separate. Historical tests have been exposed during
development and are **regression evidence**, not new unseen accuracy claims.

| Natural cohort           | Files | Exact-span F1 | Role macro F1 |
| ------------------------ | ----: | ------------: | ------------: |
| legacy                   |    11 |        87.12% |        87.32% |
| additionalFrozenFamilies |    12 |        90.91% |        92.99% |

Across all 23 natural files, F1 is 88.94%;
the separate 536-document authored focus stream is 98.14%.
Do not substitute focus or combined scores for natural-code accuracy.

| Coverage profile | Natural files | Natural exact-span F1 |
| ---------------- | ------------: | --------------------: |
| posix            |             1 |                92.97% |
| bash             |             5 |                94.29% |
| zsh              |            13 |                86.77% |
| csh              |             4 |                90.22% |

Visible Golden: **8/19** cases fully exact including modifiers.
This is a strict development probe, not a percentage of correct natural files.

## Selection and preserved history

Selected full checkpoint: `artifacts/quality-20261119/bash/expanded-window.pt`.
Parameters: **894,366**; context: **512 UTF-8 bytes**.
Refinement starts from complete historical training checkpoints, retaining
original source-family assignments, schemas, Gold and experiments.
Calibration/averaging/window policies use natural validation; train-fitted
decoder transitions use natural TRAIN Gold. Read their hash-bound provenance
and selection evidence in `model.json` and `reports/`.

The 12 additional installed Zsh function files are held-out family evidence, not new independent projects. Bash natural F1 is 94.29%; all strict Golden pass/fail outcomes retain their previous state. The original 4,423 prepared documents retain Gold and folds.

The inference artifact excludes optimizer/RNG state. Resume training only from
full `artifacts` checkpoints. Previous inference weights, reports and original
documentation are preserved in [the preceding bundle](../model-20261119-v1/BENCHMARKS.md).
