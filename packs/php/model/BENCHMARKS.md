# php quality evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match;
modifier scores remain separate. Historical tests have been exposed during
development and are **regression evidence**, not new unseen accuracy claims.

| Natural cohort | Files | Exact-span F1 | Role macro F1 |
| -------------- | ----: | ------------: | ------------: |
| legacy         |    21 |        95.55% |        92.98% |

Across all 21 natural files, F1 is 95.55%;
the separate 144-document authored focus stream is 94.28%.
Do not substitute focus or combined scores for natural-code accuracy.

| Coverage profile | Natural files | Natural exact-span F1 |
| ---------------- | ------------: | --------------------: |
| php              |            21 |                95.55% |

Visible Golden: **7/23** cases fully exact including modifiers.
This is a strict development probe, not a percentage of correct natural files.

## Selection and preserved history

Selected full checkpoint: `/Users/mystic/Codespace/neural-semantic-highlighting/artifacts/quality-20261119/remaining/php/window-reviewed.pt`.
Parameters: **895,898**; context: **512 UTF-8 bytes**.
Refinement starts from complete historical training checkpoints, retaining
original source-family assignments, schemas, Gold and experiments.
Calibration/averaging/window policies use natural validation; train-fitted
decoder transitions use natural TRAIN Gold. Read their hash-bound provenance
and selection evidence in `model.json` and `reports/`.

The inference artifact excludes optimizer/RNG state. Resume training only from
full `artifacts` checkpoints. Previous inference weights, reports and original
documentation are preserved in [the preceding bundle](../model-20261119-v1/BENCHMARKS.md).
