# JSON / JSONC baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Role macro F1
averages represented roles; declaration modifiers are separate. This measures
independent parser/source-local Gold, not compiler/type correctness, package or
framework resolution, dynamic dispatch, complete project analysis or every release.

| Evidence   | Profile | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | ------- | ------- | --------: | ------------: | ------------: |
| Validation | json    | natural |         9 |        99.93% |        99.93% |
| Validation | json    | focus   |       144 |        98.56% |        97.96% |
| Validation | jsonc   | natural |         5 |        92.90% |        82.52% |
| Validation | jsonc   | focus   |       144 |        98.27% |        97.57% |
| First test | json    | natural |         9 |        99.71% |        99.71% |
| First test | json    | focus   |       135 |        99.68% |        99.31% |
| First test | jsonc   | natural |         6 |        99.84% |        99.88% |
| First test | jsonc   | focus   |       139 |        99.46% |        98.85% |

Natural test aggregate: **99.78%** across
15 real files. Focus and combined-corpus scores
must not be presented as real-code accuracy. Small family holdouts from bounded
captures do not certify an entire language ecosystem or dependency environment.

## Data and frozen selection

204 Git-pinned original files come from Microsoft VS Code, vscode-extension-samples, TypeScript, Zed.
Original root licenses/notices, Git blob hashes and source bytes remain preserved.
The original curriculum has 52 families / 2496 variants.
JSON and JSONC curriculum variants share 40 source families; natural directory families are shared across profiles before the same exact/lexical/structural copy audit and frozen splits. Source classification happens before fixed path-hash selection, without using Golden or Playground. Original Git commit/tree/blob identities are checked independently of archive line-ending conversions. All selected bytes and licenses remain external; no schema or source commands execute. A separate 12-shared-family/576-file mixed extension follows actual validation/display review of escaped strings and block comments, preserving all 159 initial assignments and original tasks after the unchanged structural-copy audit excluded several simple-string families.
Golden, tests and displayed source never enter collection roots. Corpus/Gold /
prepared revisions remain immutable; exact and cross-family copies are audited
before windowing, and 171 source-family assignments are frozen before training.

Prepared snapshot: `4067ce51026cbe73d7a3a4ed7bc6d34075ce753c16717848320768ff7af4583d`. 2700 Gold inputs,
145 exact duplicates merged,
167 cross-family copy documents excluded,
2388 retained. Final Gold accepts 2700 files and
quarantines 0; rejected originals remain retained, never rewritten.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          134 |       1663 |    2608 |
| validation |           14 |        288 |     391 |
| test       |           15 |        274 |     377 |

Full candidate: `artifacts/json/context512-mixed-20261111-01/candidates/epoch-0006.pt`, epoch 6.
SHA-256: `9a4bcccebe6c47967498bfbb124635eb1af88194cc5a1cd6b6e25e5a77262d4e`. Fixed mean per-profile natural validation
role macro F1 (0.8347) selects within its run.
Review precedes freeze and the first adaptive test; no training follows that test.
Source, locks, licenses, every snapshot and full optimizer/RNG experiment remain
under ~/Datasets/neural-semantic-highlighting/json and artifacts/json, outside the
committed inference bundle.

## Environment and short training

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**894,872 parameters**: four layers, width 128, four heads, FFN 512, and **512 original
UTF-8 bytes** of context. Smoke precedes short three-epoch phases, initialized from
the compatible full `artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt`. All 12 non-smoke epochs take
100.2 seconds; exact invocations, resumptions and timings remain in
reports/experiments.json. Inference .pt/ONNX never initialize or resume training.

No language SDK/interpreter or global dependency is installed. Offline tooling:
Pinned Microsoft jsonc-parser 3.3.1 official npm assets with SHA-512/archive/per-file hashes, using existing Node only in project cache. Fixed revisions, original licenses/blob hashes, compiler and binary
provenance are retained. Collected source/dependencies never execute. Grammar
acceptance is not compiler validity. Parser errors, original coverage and Unicode
boundary failures quarantine input. Original CRLF and Unicode text remain unchanged.

## Real and independently visible review

Sixteen authored displays aggregate **98.84%**.
Ten actual natural validation sources were inspected before freeze; F1 ranges
92.00%–100.00%.
These are visible development diagnostics, not additional unseen test evidence.
Long upstream diagnostic excerpts are bounded in committed reports.

| Display                        | Exact-span F1 |
| ------------------------------ | ------------: |
| json/hello.json                |       100.00% |
| json/numbers.json              |        96.20% |
| json/package.json              |       100.00% |
| json/response.json             |       100.00% |
| json/schema.json               |       100.00% |
| json/strings.json              |        88.89% |
| json/theme.json                |       100.00% |
| json/unicode.json              |        94.12% |
| jsonc/comments.jsonc           |       100.00% |
| jsonc/extensions.json          |       100.00% |
| jsonc/hello.jsonc              |       100.00% |
| jsonc/launch.json              |       100.00% |
| jsonc/strings.jsonc            |        93.62% |
| jsonc/tasks.json               |       100.00% |
| jsonc/tsconfig.json            |       100.00% |
| jsonc/workspace.code-workspace |       100.00% |

The teacher passes 48 separately hand-marked Golden cases and
13 focused tests. Neural spans, roles and modifiers are entirely
exact in **35/48** Golden cases. All sixteen
examples pass the pinned parser and complete original coverage; no SDK/compiler
execution, dependency compatibility or package API validity is claimed.

Very short empty-container/primitive and comment-plus-container snippets can merge spans or misclassify keywords. Quoted-key/value roles, escapes and long string/comment boundaries across the 512-byte context remain approximate. No schema/type validation, JSON5 syntax, embedded-string parsing, automatic format detection or runtime parser/spelling repair is provided. JSONC explicitly accepts trailing commas; strict JSON supervision rejects them and comments, while runtime highlighting itself is not a syntax validator. No runtime parser, regular expression or source-spelling
repair masks prediction errors. Browser/native parity and original-text checks
establish consistent execution rather than perfect semantics. This is a bounded
usable baseline; tuning stops after its freeze and first test.
