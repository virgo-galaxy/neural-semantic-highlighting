# R baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Role macro F1
averages represented roles; declaration modifiers are separate. This measures
independent parser/source-local Gold, not compiler/type correctness, package or
framework resolution, dynamic dispatch, complete project analysis or every release.

| Evidence   | Profile | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | ------- | ------- | --------: | ------------: | ------------: |
| Validation | r       | natural |        17 |        95.01% |        86.78% |
| Validation | r       | focus   |       112 |        93.89% |        90.52% |
| First test | r       | natural |        15 |        96.04% |        95.87% |
| First test | r       | focus   |       112 |        95.97% |        95.67% |

Natural test aggregate: **96.04%** across
15 real files. Focus and combined-corpus scores
must not be presented as real-code accuracy. Small family holdouts from bounded
captures do not certify an entire language ecosystem or dependency environment.

## Data and frozen selection

144 Git-pinned original files come from dplyr, ggplot2, tidyr, purrr.
Original root licenses/notices, Git blob hashes and source bytes remain preserved.
The original curriculum has 50 families / 1200 variants.
Golden, tests and displayed source never enter collection roots. Corpus/Gold /
prepared revisions remain immutable; exact and cross-family copies are audited
before windowing, and 133 source-family assignments are frozen before training.

Prepared snapshot: `50f1340c7c662ebd13a064f9258ac2715f77287ca33bf4d27ae4d598100f6213`. 1344 Gold inputs,
73 exact duplicates merged,
60 cross-family copy documents excluded,
1211 retained. Final Gold accepts 1344 files and
quarantines 0; rejected originals remain retained, never rewritten.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          112 |        843 |    1943 |
| validation |           17 |        112 |     247 |
| test       |           15 |        112 |     247 |

Full candidate: `artifacts/r/context512-20261111-01/candidates/epoch-0005.pt`, epoch 5.
SHA-256: `6aa5a0b033e515fb7377e8e5f6374a8a7d0b84566cc19f334967008d55f3a76c`. Fixed mean per-profile natural validation
role macro F1 (0.9172) selects within its run.
Review precedes freeze and the first adaptive test; no training follows that test.
Source, locks, licenses, every snapshot and full optimizer/RNG experiment remain
under ~/Datasets/neural-semantic-highlighting/r and artifacts/r, outside the
committed inference bundle.

## Environment and short training

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**894,872 parameters**: four layers, width 128, four heads, FFN 512, and **512 original
UTF-8 bytes** of context. Smoke precedes short three-epoch phases, initialized from
the compatible full `artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt`. All 6 non-smoke epochs take
82.3 seconds; exact invocations, resumptions and timings remain in
reports/experiments.json. Inference .pt/ONNX never initialize or resume training.

No language SDK/interpreter or global dependency is installed. Offline tooling:
r-lib tree-sitter-r 1.3.0 and Tree-sitter 0.25.10, compiled with existing Clang only in project cache. Fixed revisions, original licenses/blob hashes, compiler and binary
provenance are retained. Collected source/dependencies never execute. Grammar
acceptance is not compiler validity. Parser errors, original coverage and Unicode
boundary failures quarantine input. Original CRLF and Unicode text remain unchanged.

## Real and independently visible review

Eight authored displays aggregate **92.52%**.
Ten actual natural validation sources were inspected before freeze; F1 ranges
91.22%–98.82%.
These are visible development diagnostics, not additional unseen test evidence.
Long upstream diagnostic excerpts are bounded in committed reports.

| Display     | Exact-span F1 |
| ----------- | ------------: |
| frames.R    |        96.45% |
| functions.R |        94.55% |
| hello.R     |        92.31% |
| models.R    |        96.94% |
| objects.R   |        96.48% |
| pipeline.R  |        88.24% |
| plot.R      |        94.74% |
| strings.R   |        73.33% |

The teacher passes 32 separately hand-marked Golden cases and
10 focused tests. Neural spans, roles and modifiers are entirely
exact in **13/32** Golden cases. All eight
examples pass the pinned parser and complete original coverage; no SDK/compiler
execution, dependency compatibility or package API validity is claimed.

Long raw/delimited strings, backtick names, comments, closure and dynamic-call roles remain approximate. Formula names, tidy evaluation/NSE, environments/promises and S3/S4 dispatch are source-local approximations, without R package/type resolution. No runtime parser, regular expression or source-spelling
repair masks prediction errors. Browser/native parity and original-text checks
establish consistent execution rather than perfect semantics. This is a bounded
usable baseline; tuning stops after its freeze and first test.
