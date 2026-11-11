# Ruby baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Role macro F1
averages represented roles; declaration modifiers are separate. This measures
independent parser/source-local Gold, not compiler/type correctness, package or
framework resolution, dynamic dispatch, complete project analysis or every release.

| Evidence   | Profile | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | ------- | ------- | --------: | ------------: | ------------: |
| Validation | ruby    | natural |        16 |        88.99% |        82.99% |
| Validation | ruby    | focus   |       139 |        93.54% |        94.23% |
| First test | ruby    | natural |        15 |        86.96% |        81.02% |
| First test | ruby    | focus   |       134 |        92.56% |        92.43% |

Natural test aggregate: **86.96%** across
15 real files. Focus and combined-corpus scores
must not be presented as real-code accuracy. Small family holdouts from bounded
captures do not certify an entire language ecosystem or dependency environment.

## Data and frozen selection

170 Git-pinned original files come from Rails Active Support, Rake, Rack, RSpec Core.
Original root licenses/notices, Git blob hashes and source bytes remain preserved.
The original curriculum has 68 families / 1632 variants.
Initial Gold quarantined 15 files because the CST hides explicit backslash-newline extras. A bounded original-gap adapter and independent Golden/regression restore these ranges before the first training run. Initial snapshots remain preserved; final Gold has zero quarantines. Nonempty CST heredoc endings are required, including for quoted and multiple heredocs; input code and subshells never execute. A separate 12-family/288-task mixed extension addresses qualified names, instance calls, pattern/heredoc and mixed-literal review, preserving all 210 original family assignments and the initial curriculum.
Golden, tests and displayed source never enter collection roots. Corpus/Gold /
prepared revisions remain immutable; exact and cross-family copies are audited
before windowing, and 222 source-family assignments are frozen before training.

Prepared snapshot: `eac5401f3798c11f531a1d95f6d5033e6cc66f3eda50b95d1131e601d6bc5412`. 1802 Gold inputs,
105 exact duplicates merged,
40 cross-family copy documents excluded,
1657 retained. Final Gold accepts 1802 files and
quarantines 0; rejected originals remain retained, never rewritten.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          139 |       1214 |    2132 |
| validation |           16 |        139 |     252 |
| test       |           15 |        134 |     246 |

Full candidate: `artifacts/ruby/context512-mixed-20261111-01/candidates/epoch-0005.pt`, epoch 5.
SHA-256: `3580472f6f5ebef2208dd38114cd721694c11551c95d7dd716f18f78421a5311`. Fixed mean per-profile natural validation
role macro F1 (0.8218) selects within its run.
Review precedes freeze and the first adaptive test; no training follows that test.
Source, locks, licenses, every snapshot and full optimizer/RNG experiment remain
under ~/Datasets/neural-semantic-highlighting/ruby and artifacts/ruby, outside the
committed inference bundle.

## Environment and short training

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**894,872 parameters**: four layers, width 128, four heads, FFN 512, and **512 original
UTF-8 bytes** of context. Smoke precedes short three-epoch phases, initialized from
the compatible full `artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt`. All 15 non-smoke epochs take
186.3 seconds; exact invocations, resumptions and timings remain in
reports/experiments.json. Inference .pt/ONNX never initialize or resume training.

No language SDK/interpreter or global dependency is installed. Offline tooling:
Tree-sitter Ruby 0.23.1 at ad907a69 with runtime 0.25.10, compiled with existing Clang only in project cache. Fixed revisions, original licenses/blob hashes, compiler and binary
provenance are retained. Collected source/dependencies never execute. Grammar
acceptance is not compiler validity. Parser errors, original coverage and Unicode
boundary failures quarantine input. Original CRLF and Unicode text remain unchanged.

## Real and independently visible review

Eight authored displays aggregate **90.62%**.
Ten actual natural validation sources were inspected before freeze; F1 ranges
82.74%–100.00%.
These are visible development diagnostics, not additional unseen test evidence.
Long upstream diagnostic excerpts are bounded in committed reports.

| Display        | Exact-span F1 |
| -------------- | ------------: |
| blocks.rb      |        94.63% |
| classes.rb     |        95.76% |
| collections.rb |        88.58% |
| hello.rb       |        91.07% |
| heredoc.rb     |        81.63% |
| patterns.rb    |        88.89% |
| rails.rb       |        90.64% |
| strings.rb     |        90.00% |

The teacher passes 33 separately hand-marked Golden cases and
13 focused tests. Neural spans, roles and modifiers are entirely
exact in **10/33** Golden cases. All eight
examples pass the pinned parser and complete original coverage; no SDK/compiler
execution, dependency compatibility or package API validity is claimed.

Heredoc/percent/regex/interpolated string boundaries, destructuring/pattern bindings, constant/type and top-level/member call roles remain approximate. Dynamic dispatch, metaprogramming, Rails/Rake DSLs, generated classes, refinements and distant scopes are source-local approximations without Ruby/gem execution or dependency resolution. No runtime parser, regular expression or source-spelling
repair masks prediction errors. Browser/native parity and original-text checks
establish consistent execution rather than perfect semantics. This is a bounded
usable baseline; tuning stops after its freeze and first test.
