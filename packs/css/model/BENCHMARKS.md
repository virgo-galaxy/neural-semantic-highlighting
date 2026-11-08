# CSS family benchmark

## Protocol

An exact span matches document, UTF-16 start, end and semantic type. The separate
modifier-aware metric additionally requires the complete declaration-modifier
set. Micro F1 pools span counts within one document kind. Macro F1 averages roles
with any Gold or predicted support; a role predicted without Gold support scores
zero. Zero-support roles are not evidence of accuracy.

Training validation batches fixed, Unicode-safe byte windows and reassembles
whole-document logits before decoding. Its cuts do not use Gold. Selection uses
the mean of CSS/SCSS/Less exact-span macro F1. Independent final evaluation uses
the real predicted-adaptive cursor: no Gold cuts, parser, lexical scaffold,
overlap fusion or post-hoc source correction.

| Split/backend            | CSS F1 | SCSS F1 | Less F1 |
| ------------------------ | -----: | ------: | ------: |
| Validation, adaptive CPU | 98.25% |  98.56% |  99.35% |
| Test, adaptive MPS       | 99.04% |  99.40% |  99.42% |

Validation contains 16 CSS, 14 SCSS and 20 Less documents. Test contains 5 CSS,
28 SCSS and 26 Less documents. The backend differs between the archived validation
and test reports; these are not a cross-backend numerical-equivalence benchmark.
The test evaluation took 4.32 seconds inside the evaluator, including initial MPS
forward setup. This is not a steady-state latency or browser-performance claim.

## Data identity and isolation

Prepared snapshot:
`237f8d8278ef5797976a91f19e1fd6cda95bd31bc528503bf0aed9e529d8f697`.
The exact manifest hash and file checksums are archived with the selected model.

Source allowlists include existing local corpora, NSH application/theme styles,
Bootstrap 5.3.8, Bulma 1.0.4, Ant Design 4.24.16 and Pico 2.1.1. The four npm
archives are integrity-checked and only their selected style/license files are
retained. Imports, package scripts and preprocessors are never executed.

Of 790 captured documents, 786 receive complete offline Gold; four parser failures
are quarantined with their original source. There are 671 unique documents after
115 exact duplicate records are merged. Another 151 documents sharing lexical or
normalized-shape fingerprints across source directories are excluded with an
audit. The remaining 520 documents in 156 source-directory groups split intact
before windowing:

| Split      | Documents | Windows |
| ---------- | --------: | ------: |
| Train      |       411 |   2,653 |
| Validation |        50 |     327 |
| Test       |        59 |     328 |

Training uses Gold-adaptive windows. Evaluation uses fixed non-Gold windows or
actual predicted adaptive inference as identified in each report. A balanced
epoch presents 4,122 windows by cycling minority document kinds; this repetition
is not additional independent data. Loss weights count each unique train window
once. Padding and UTF-8 continuation bytes are ignored; modifiers are supervised
at span beginnings only.

Golden and Playground demonstration sources are excluded from collection. The
independently marked, visible probes cover 11 development cases; they are used
for inspection and must not be described as a held-out corpus estimate. Only
four are entirely exact including modifiers in this candidate. The Surface layout
has one wrong type, `auto-fit` as variable instead of keyword. Detailed missing
and unexpected spans remain in `reports/golden-probes.json`.

## Reproduce

Use the frozen external snapshot and its original training checkpoint, not the
selected inference artifact, when reproducing checkpoint-bound reports:

```bash
make evaluate-css CSS_CHECKPOINT=artifacts/css/context512-modern-grid-20261108-01/best.pt
make evaluate-css CSS_CHECKPOINT=artifacts/css/context512-modern-grid-20261108-01/best.pt CSS_EVAL_SPLIT=test CSS_DEVICE=mps
make challenge-css CSS_CHECKPOINT=artifacts/css/context512-modern-grid-20261108-01/best.pt
```

Do not repeatedly tune against held-out test. `reports/test-metrics.json` is the
candidate's first independent test. All reports bind the exact source checkpoint
hash and epoch; model metadata records the separate inference-export hash.
Earlier snapshots, the 13-epoch from-scratch run and the first Go-initialized
8-epoch experiment are retained in external data and ignored artifacts. Their
validation splits differ from this snapshot and are not directly comparable.
