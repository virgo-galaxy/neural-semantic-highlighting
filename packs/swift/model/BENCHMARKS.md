# swift quality evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match;
modifier scores remain separate. Historical tests have been exposed during
development and are **regression evidence**, not new unseen accuracy claims.

| Natural cohort | Files | Exact-span F1 | Role macro F1 |
| -------------- | ----: | ------------: | ------------: |
| legacy         |    22 |        94.52% |        86.94% |

Across all 22 natural files, F1 is 94.52%;
the separate 159-document authored focus stream is 95.85%.
Do not substitute focus or combined scores for natural-code accuracy.

| Coverage profile | Natural files | Natural exact-span F1 |
| ---------------- | ------------: | --------------------: |
| swift            |            22 |                94.52% |

Visible Golden: **14/28** cases fully exact including modifiers.
This is a strict development probe, not a percentage of correct natural files.

## Selection and preserved history

Selected full checkpoint: `/Users/mystic/Codespace/neural-semantic-highlighting/artifacts/quality-20261119/remaining/swift/window-reviewed.pt`.
Parameters: **894,872**; context: **512 UTF-8 bytes**.
Refinement starts from complete historical training checkpoints, retaining
original source-family assignments, schemas, Gold and experiments.
Calibration/averaging/window policies use natural validation; train-fitted
decoder transitions use natural TRAIN Gold. Read their hash-bound provenance
and selection evidence in `model.json` and `reports/`.

The inference artifact excludes optimizer/RNG state. Resume training only from
full `artifacts` checkpoints. Previous inference weights, reports and original
documentation are preserved in [the preceding bundle](../model-20261119-v1/BENCHMARKS.md).
