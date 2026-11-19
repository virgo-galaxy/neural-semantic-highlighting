# bat quality evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match;
modifier scores remain separate. Historical tests have been exposed during
development and are **regression evidence**, not new unseen accuracy claims.

| Natural cohort           | Files | Exact-span F1 | Role macro F1 |
| ------------------------ | ----: | ------------: | ------------: |
| legacy                   |     3 |        90.61% |        88.35% |
| additionalFrozenFamilies |     6 |        75.36% |        58.99% |

Across all 9 natural files, F1 is 81.69%;
the separate 234-document authored focus stream is 96.69%.
Do not substitute focus or combined scores for natural-code accuracy.

| Coverage profile | Natural files | Natural exact-span F1 |
| ---------------- | ------------: | --------------------: |
| bat              |             9 |                81.69% |

Visible Golden: **9/12** cases fully exact including modifiers.
This is a strict development probe, not a percentage of correct natural files.

## Selection and preserved history

Selected full checkpoint: `/Users/mystic/Codespace/neural-semantic-highlighting/artifacts/quality-20261119/bat/window-reviewed.pt`.
Parameters: **894,350**; context: **512 UTF-8 bytes**.
Refinement starts from complete historical training checkpoints, retaining
original source-family assignments, schemas, Gold and experiments.
Calibration/averaging/window policies use natural validation; train-fitted
decoder transitions use natural TRAIN Gold. Read their hash-bound provenance
and selection evidence in `model.json` and `reports/`.

Additional frozen-family tests were first read on an earlier candidate in this
optimization session; the final values above are now exposed follow-up results.
They must not be relabelled as another fresh independent test.

The added six-script project holdout is harder and still below 90%. Improvement
on three old scripts does not establish universal Windows batch accuracy.

The inference artifact excludes optimizer/RNG state. Resume training only from
full `artifacts` checkpoints. Previous inference weights, reports and original
documentation are preserved in [the preceding bundle](../model-20261119-v1/BENCHMARKS.md).
