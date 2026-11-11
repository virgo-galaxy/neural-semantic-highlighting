# Scala baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Role macro F1
averages represented roles; declaration modifiers are separate. This measures
independent parser/source-local Gold, not compiler/type correctness, package or
framework resolution, dynamic dispatch, complete project analysis or every release.

| Evidence   | Profile | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | ------- | ------- | --------: | ------------: | ------------: |
| Validation | scala   | natural |        23 |        92.56% |        79.67% |
| Validation | scala   | focus   |       112 |        97.04% |        92.87% |
| First test | scala   | natural |        30 |        89.00% |        76.05% |
| First test | scala   | focus   |       112 |        98.07% |        85.85% |

Natural test aggregate: **89.00%** across
30 real files. Focus and combined-corpus scores
must not be presented as real-code accuracy. Small family holdouts from bounded
captures do not certify an entire language ecosystem or dependency environment.

## Data and frozen selection

180 Git-pinned original files come from Scala 2 standard library, Scala 3 library, Cats, Ox, Kyo.
Original root licenses/notices, Git blob hashes and source bytes remain preserved.
The original curriculum has 54 families / 1296 variants.
Twenty-one captured files (including one Kyo source) in shared reserved paths remain preserved but excluded by the collector. Before any neural test, 24 new Kyo source files were reserved as one whole-project Scala 3 test family, preserving all 95 earlier assignments. The initial parser adapter quarantined 33 files because the CST omitted end keywords; the corrected adapter and independent regression restore their original ranges. Initial Gold/experiments remain preserved; final Gold has no quarantines. See collector-exclusions.json and heldout-project.json in reports.
Golden, tests and displayed source never enter collection roots. Corpus/Gold /
prepared revisions remain immutable; exact and cross-family copies are audited
before windowing, and 96 source-family assignments are frozen before training.

Prepared snapshot: `c700ffe8137878451bd1fcf0d4989c807b283f2cee08de928e2ebbc68bcf1d65`. 1455 Gold inputs,
89 exact duplicates merged,
40 cross-family copy documents excluded,
1326 retained. Final Gold accepts 1455 files and
quarantines 0; rejected originals remain retained, never rewritten.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          106 |        943 |    1948 |
| validation |           23 |        112 |     264 |
| test       |           30 |        112 |     345 |

Full candidate: `artifacts/scala/context512-expanded-20261111-01/candidates/epoch-0005.pt`, epoch 5.
SHA-256: `c917b64cfecbf340045eae625088e2722718af81e1943e91522900aae0c043b6`. Fixed mean per-profile natural validation
role macro F1 (0.7753) selects within its run.
Review precedes freeze and the first adaptive test; no training follows that test.
Source, locks, licenses, every snapshot and full optimizer/RNG experiment remain
under ~/Datasets/neural-semantic-highlighting/scala and artifacts/scala, outside the
committed inference bundle.

## Environment and short training

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**894,872 parameters**: four layers, width 128, four heads, FFN 512, and **512 original
UTF-8 bytes** of context. Smoke precedes short three-epoch phases, initialized from
the compatible full `artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt`. All 12 non-smoke epochs take
143.5 seconds; exact invocations, resumptions and timings remain in
reports/experiments.json. Inference .pt/ONNX never initialize or resume training.

No language SDK/interpreter or global dependency is installed. Offline tooling:
Tree-sitter Scala 0.26.12 with runtime 0.25.10, compiled with existing Clang only in project cache. Fixed revisions, original licenses/blob hashes, compiler and binary
provenance are retained. Collected source/dependencies never execute. Grammar
acceptance is not compiler validity. Parser errors, original coverage and Unicode
boundary failures quarantine input. Original CRLF and Unicode text remain unchanged.

## Real and independently visible review

Eight authored displays aggregate **90.13%**.
Ten actual natural validation sources were inspected before freeze; F1 ranges
85.71%–100.00%.
These are visible development diagnostics, not additional unseen test evidence.
Long upstream diagnostic excerpts are bounded in committed reports.

| Display           | Exact-span F1 |
| ----------------- | ------------: |
| async.scala       |        93.25% |
| collections.scala |        94.92% |
| contextual.scala  |        94.23% |
| generics.scala    |        88.89% |
| hello.scala       |        88.00% |
| models.scala      |        85.03% |
| scala2.scala      |        95.51% |
| strings.scala     |        72.26% |

The teacher passes 33 separately hand-marked Golden cases and
13 focused tests. Neural spans, roles and modifiers are entirely
exact in **17/33** Golden cases. All eight
examples pass the pinned parser and complete original coverage; no SDK/compiler
execution, dependency compatibility or package API validity is claimed.

Long plain/raw/interpolated strings, generic/type and enum/constructor roles, implicit receivers and distant symbols remain approximate. Given/using and extension syntax is source-local, without implicit search, overload resolution, macro/plugin execution, framework APIs or experimental type-system certification. No runtime parser, regular expression or source-spelling
repair masks prediction errors. Browser/native parity and original-text checks
establish consistent execution rather than perfect semantics. This is a bounded
usable baseline; tuning stops after its freeze and first test.

## Breakdown of the same first natural test

This post-freeze source breakdown exactly reproduces the natural-test aggregate.
It is not additional selection evidence, and no training follows it.

| Source         | Files | Exact-span F1 |
| -------------- | ----: | ------------: |
| kyo-scala-v1   |    23 |        87.14% |
| scala-scala-v1 |     7 |        92.51% |

The independent Kyo project stresses effect types, higher-kinded/contextual code,
macros and deep scopes. Its whole-project holdout is materially harder than the
common Scala 2/3 display probes. The aggregate is not a universal Scala score.
