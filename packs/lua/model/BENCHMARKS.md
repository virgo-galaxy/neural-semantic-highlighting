# Lua baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Role macro F1
averages represented roles; declaration modifiers are separate. This measures
independent parser/source-local Gold, not compiler/type correctness, package or
framework resolution, dynamic dispatch, complete project analysis or every release.

| Evidence   | Profile | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | ------- | ------- | --------: | ------------: | ------------: |
| Validation | lua     | natural |        16 |        92.00% |        83.01% |
| Validation | lua     | focus   |       115 |        93.79% |        85.31% |
| First test | lua     | natural |        15 |        91.78% |        89.22% |
| First test | lua     | focus   |       112 |        95.41% |        86.16% |

Natural test aggregate: **91.78%** across
15 real files. Focus and combined-corpus scores
must not be presented as real-code accuracy. Small family holdouts from bounded
captures do not certify an entire language ecosystem or dependency environment.

## Data and frozen selection

155 Git-pinned original files come from Neovim, Penlight, plenary.nvim, LuaRocks.
Original root licenses/notices, Git blob hashes and source bytes remain preserved.
The original curriculum has 52 families / 1248 variants.

Golden, tests and displayed source never enter collection roots. Corpus/Gold /
prepared revisions remain immutable; exact and cross-family copies are audited
before windowing, and 195 source-family assignments are frozen before training.

Prepared snapshot: `eda372707fea49e2f81c258976e0741534a615f7b20be18ec3814cef7385f8eb`. 1403 Gold inputs,
71 exact duplicates merged,
60 cross-family copy documents excluded,
1272 retained. Final Gold accepts 1403 files and
quarantines 0; rejected originals remain retained, never rewritten.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          124 |        890 |    2105 |
| validation |           16 |        115 |     264 |
| test       |           15 |        112 |     261 |

Full candidate: `artifacts/lua/context512-20261111-01/candidates/epoch-0003.pt`, epoch 3.
SHA-256: `ac38fddc0c2051b7be1bb855b608d56c76aed6f1f40ecab9b440d0460a4908ed`. Fixed mean per-profile natural validation
role macro F1 (0.7507) selects within its run.
Review precedes freeze and the first adaptive test; no training follows that test.
Source, locks, licenses, every snapshot and full optimizer/RNG experiment remain
under ~/Datasets/neural-semantic-highlighting/lua and artifacts/lua, outside the
committed inference bundle.

## Environment and short training

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**894,872 parameters**: four layers, width 128, four heads, FFN 512, and **512 original
UTF-8 bytes** of context. Smoke precedes short three-epoch phases, initialized from
the compatible full `artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt`. All 6 non-smoke epochs take
96.9 seconds; exact invocations, resumptions and timings remain in
reports/experiments.json. Inference .pt/ONNX never initialize or resume training.

No language SDK/interpreter or global dependency is installed. Offline tooling:
Tree-sitter Lua 0.5.0 at 10fe0054 with runtime 0.25.10, compiled with existing Clang only in project cache. Fixed revisions, original licenses/blob hashes, compiler and binary
provenance are retained. Collected source/dependencies never execute. Grammar
acceptance is not compiler validity. Parser errors, original coverage and Unicode
boundary failures quarantine input. Original CRLF and Unicode text remain unchanged.

## Real and independently visible review

Eight authored displays aggregate **92.28%**.
Ten actual natural validation sources were inspected before freeze; F1 ranges
82.80%–98.59%.
These are visible development diagnostics, not additional unseen test evidence.
Long upstream diagnostic excerpts are bounded in committed reports.

| Display      | Exact-span F1 |
| ------------ | ------------: |
| closures.lua |        88.61% |
| hello.lua    |        94.44% |
| loops.lua    |        97.18% |
| modern.lua   |        81.01% |
| modules.lua  |        93.00% |
| neovim.lua   |        97.17% |
| strings.lua  |        90.24% |
| tables.lua   |        94.94% |

The teacher passes 32 separately hand-marked Golden cases and
13 focused tests. Neural spans, roles and modifiers are entirely
exact in **10/32** Golden cases. All eight
examples pass the pinned parser and complete original coverage; no SDK/compiler
execution, dependency compatibility or package API validity is claimed.

Long/delimited string and comment boundaries, table/method roles, closure captures, dynamic metatables and distant lexical bindings remain approximate. No Lua/Neovim/LuaRocks execution, dependency resolution or full LuaJIT/Luau dialect compatibility is claimed. No runtime parser, regular expression or source-spelling
repair masks prediction errors. Browser/native parity and original-text checks
establish consistent execution rather than perfect semantics. This is a bounded
usable baseline; tuning stops after its freeze and first test.
