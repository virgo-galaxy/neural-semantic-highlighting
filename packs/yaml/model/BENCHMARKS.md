# YAML baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Role macro F1
averages represented roles; anchor declaration modifiers are separate. It measures
independently composed YAML/CST ranges and source-local roles, not application
schema validity, alias/merge expansion, template execution or syntax validation
by the runtime highlighter.

| Evidence   | Profile | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | ------- | ------- | --------: | ------------: | ------------: |
| Validation | yaml    | natural |        11 |        87.15% |        82.35% |
| Validation | yaml    | focus   |       120 |        93.02% |        69.35% |
| First test | yaml    | natural |        12 |        95.34% |        92.66% |
| First test | yaml    | focus   |       144 |        92.65% |        72.54% |

Natural test aggregate: **95.34%** across
12 real files. Focus and combined-corpus scores
must not be presented as real-code accuracy. Small family holdouts from bounded
captures do not certify an entire language ecosystem or dependency environment.

## Data and frozen selection

152 Git-pinned original files come from Kubernetes examples, Docker awesome-compose, Prometheus, GitHub Actions starter workflows.
Original root licenses/notices, Git blob hashes and source bytes remain preserved.
The original curriculum has 53 families / 1272 variants.
Original Git commit/tree/blob identities and licenses are preserved. Fixed parser/CST validation happens before path-hash bounded selection; rejected candidates are retained in source-selection metadata. Parser supervision does not execute configuration commands, resolve aliases or load application schemas. A separate eight-family/192-task mixed extension follows actual validation/display review of block-header/body, comment and anchor contexts, preserving all 161 original assignments and the initial corpus/run.
Golden, tests and displayed source never enter collection roots. Corpus/Gold /
prepared revisions remain immutable; exact and cross-family copies are audited
before windowing, and 169 source-family assignments are frozen before training.

Prepared snapshot: `3b086269574928ec58cdd520897e523eda46bb21be1eebff73f6ec8401747b2c`. 1424 Gold inputs,
5 exact duplicates merged,
14 cross-family copy documents excluded,
1405 retained. Final Gold accepts 1424 files and
quarantines 0; rejected originals remain retained, never rewritten.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          115 |       1003 |    1591 |
| validation |           11 |        120 |     165 |
| test       |           12 |        144 |     189 |

Full candidate: `artifacts/yaml/context512-refine-20261112-01/candidates/epoch-0003.pt`, epoch 3.
SHA-256: `61ab25b3ecfc7a8f47a779ab0b14ddacef1927d3198b79e4e209f69549e711ec`. Fixed mean per-profile natural validation
role macro F1 (0.7744) selects within its run.
Review precedes freeze and the first adaptive test; no training follows that test.
Source, locks, licenses, every snapshot and full optimizer/RNG experiment remain
under ~/Datasets/neural-semantic-highlighting/yaml and artifacts/yaml, outside the
committed inference bundle.

## Environment and short training

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**894,872 parameters**: four layers, width 128, four heads, FFN 512, and **512 original
UTF-8 bytes** of context. Smoke precedes short three-epoch phases, initialized from
the compatible full `artifacts/json/context512-mixed-20261111-01/candidates/epoch-0006.pt`. All 18 non-smoke epochs take
97.6 seconds; exact invocations, resumptions and timings remain in
reports/experiments.json. Inference .pt/ONNX never initialize or resume training.

No language SDK/interpreter or global dependency is installed. Offline tooling:
Pinned yaml 2.9.1 official npm Document/CST assets with archive/per-file hashes and retained ISC license, using existing Node only in project cache. Fixed revisions, original licenses/blob hashes, compiler and binary
provenance are retained. Collected source/dependencies never execute. Grammar
acceptance is not compiler validity. Parser errors, original coverage and Unicode
boundary failures quarantine input. Original CRLF and Unicode text remain unchanged.

## Real and independently visible review

Eight authored displays aggregate **94.44%**.
Ten actual natural validation sources were inspected before freeze; F1 ranges
56.10%–100.00%.
These are visible development diagnostics, not additional unseen test evidence.
Long upstream diagnostic excerpts are bounded in committed reports.

| Display         | Exact-span F1 |
| --------------- | ------------: |
| anchors.yaml    |        91.11% |
| blocks.yaml     |        58.54% |
| compose.yaml    |       100.00% |
| documents.yaml  |        91.26% |
| hello.yaml      |       100.00% |
| kubernetes.yaml |        98.63% |
| monitoring.yml  |        97.96% |
| workflow.yml    |        96.15% |

The teacher passes 40 separately hand-marked Golden cases and
14 focused tests. Neural spans, roles and modifiers are entirely
exact in **15/40** Golden cases. All eight
examples pass the pinned parser and complete original coverage; no SDK/compiler
execution, dependency compatibility or package API validity is claimed.

Block scalars remain a material weakness: header comments can merge into bodies, indented # lines can receive comment roles, folded bodies can fragment, and JSON-looking literal content can acquire nested property/keyword roles even within the context. Plain/quoted/block scalar and header boundaries, indentation-sensitive key/value roles, anchors/aliases/tags and multi-document context remain approximate. No alias expansion, schema/application validation, legacy YAML 1.1 type guarantee, template execution, embedded-language parsing or runtime parser/spelling repair is provided. No runtime parser, regular expression or source-spelling
repair masks prediction errors. Browser/native parity and original-text checks
establish consistent execution rather than perfect semantics. This is a bounded
usable baseline; tuning stops after its freeze and first test.
