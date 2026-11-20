# ruby quality evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match;
modifier scores remain separate. Historical tests have been exposed during
development and are **regression evidence**, not new unseen accuracy claims.

| Natural cohort           | Files | Exact-span F1 | Role macro F1 |
| ------------------------ | ----: | ------------: | ------------: |
| legacy                   |    15 |        90.60% |        86.36% |
| additionalFrozenFamilies |    11 |        94.41% |        93.46% |

Across all 26 natural files, F1 is 92.59%;
the separate 134-document authored focus stream is 93.88%.
Do not substitute focus or combined scores for natural-code accuracy.

| Coverage profile | Natural files | Natural exact-span F1 |
| ---------------- | ------------: | --------------------: |
| ruby             |            26 |                92.59% |

Visible Golden: **12/33** cases fully exact including modifiers.
This is a strict development probe, not a percentage of correct natural files.

## Selection and preserved history

Selected full checkpoint: `artifacts/quality-20261119/ruby/expanded-window.pt`.
Parameters: **895,656**; context: **512 UTF-8 bytes**.
Refinement starts from complete historical training checkpoints, retaining
original source-family assignments, schemas, Gold and experiments.
Calibration/averaging/window policies use natural validation; train-fitted
decoder transitions use natural TRAIN Gold. Read their hash-bound provenance
and selection evidence in `model.json` and `reports/`.

The 11 additional pinned upstream files were frozen before training expansion. The original 15-file cohort remains separate from them. All 1,657 original prepared documents retain Gold and folds.

The inference artifact excludes optimizer/RNG state. Resume training only from
full `artifacts` checkpoints. Previous inference weights, reports and original
documentation are preserved in [the preceding bundle](../model-20261119-v1/BENCHMARKS.md).
