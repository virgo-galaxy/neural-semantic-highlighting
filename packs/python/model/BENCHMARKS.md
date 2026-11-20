# python quality evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match;
modifier scores remain separate. Historical tests have been exposed during
development and are **regression evidence**, not new unseen accuracy claims.

| Natural cohort           | Files | Exact-span F1 | Role macro F1 |
| ------------------------ | ----: | ------------: | ------------: |
| legacy                   |     4 |        91.48% |        85.98% |
| additionalFrozenFamilies |    19 |        90.87% |        88.23% |

Across all 23 natural files, F1 is 91.03%;
the separate 92-document authored focus stream is 96.34%.
Do not substitute focus or combined scores for natural-code accuracy.

| Coverage profile | Natural files | Natural exact-span F1 |
| ---------------- | ------------: | --------------------: |
| python3          |            23 |                91.03% |

Visible Golden: **4/10** cases fully exact including modifiers.
This is a strict development probe, not a percentage of correct natural files.

## Selection and preserved history

Selected full checkpoint: `artifacts/quality-20261119/python/window-reviewed.pt`.
Parameters: **895,398**; context: **512 UTF-8 bytes**.
Refinement starts from complete historical training checkpoints, retaining
original source-family assignments, schemas, Gold and experiments.
Calibration/averaging/window policies use natural validation; train-fitted
decoder transitions use natural TRAIN Gold. Read their hash-bound provenance
and selection evidence in `model.json` and `reports/`.

Additional frozen-family tests were first read on an earlier candidate in this
optimization session; the final values above are now exposed follow-up results.
They must not be relabelled as another fresh independent test.

The inference artifact excludes optimizer/RNG state. Resume training only from
full `artifacts` checkpoints. Previous inference weights, reports and original
documentation are preserved in [the preceding bundle](../model-20261119-v1/BENCHMARKS.md).
