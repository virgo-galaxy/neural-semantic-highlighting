# makefile quality evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match;
modifier scores remain separate. Historical tests have been exposed during
development and are **regression evidence**, not new unseen accuracy claims.

| Natural cohort | Files | Exact-span F1 | Role macro F1 |
| -------------- | ----: | ------------: | ------------: |
| fresh          |    16 |        94.57% |        95.94% |
| legacy         |    17 |        94.12% |        91.64% |

Across all 33 natural files, F1 is 94.37%;
the separate 180-document authored focus stream is 98.95%.
Do not substitute focus or combined scores for natural-code accuracy.

| Coverage profile | Natural files | Natural exact-span F1 |
| ---------------- | ------------: | --------------------: |
| makefile         |            33 |                94.37% |

Visible Golden: **26/46** cases fully exact including modifiers.
This is a strict development probe, not a percentage of correct natural files.

## Selection and preserved history

Selected full checkpoint: `/Users/mystic/Codespace/neural-semantic-highlighting/artifacts/quality-20261119/remaining/makefile/greedy-window.pt`.
Parameters: **894,479**; context: **512 UTF-8 bytes**.
Refinement starts from complete historical training checkpoints, retaining
original source-family assignments, schemas, Gold and experiments.
Calibration/averaging/window policies use natural validation; train-fitted
decoder transitions use natural TRAIN Gold. Read their hash-bound provenance
and selection evidence in `model.json` and `reports/`.

The selected revision retains the earlier neural weights and decoder, adding validation-selected windows. A higher-scoring fine-tuned candidate was rejected because inline recipes and source without a final newline regressed. All 26 previously exact Golden cases remain exact. The historical fresh/legacy cohorts keep their original membership and are now both exposed regressions.

The inference artifact excludes optimizer/RNG state. Resume training only from
full `artifacts` checkpoints. Previous inference weights, reports and original
documentation are preserved in [the preceding bundle](../model-20261119-v1/BENCHMARKS.md).
