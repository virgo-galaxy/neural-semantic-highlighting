# Rust baseline evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match.
Role macro F1 averages represented roles; declaration modifiers are separate.
This measures bounded syntax/source-local bindings, not rustc project semantics,
borrow checking, macro expansion or whole-project type inference. Natural sources,
focused tasks and visible display code are distinct evidence.

| Evidence           | Documents | Exact-span F1 | Role macro F1 |
| ------------------ | --------: | ------------: | ------------: |
| Natural validation |        15 |        90.74% |        79.61% |
| Focus validation   |       154 |        93.89% |        74.94% |
| First natural test |        15 |        94.90% |        79.62% |
| First focus test   |       131 |        92.16% |        75.50% |

Frozen full candidate: `artifacts/rust/context512-literals-20261110-01/candidates/epoch-0004.pt`, epoch 4 of the literal revision.
Fixed natural validation role macro F1 (0.7891) selects
within this run. Natural validation files, independent Golden and display code were
reviewed before first adaptive test. No training followed that test; these results
are now known evidence for future revisions. Do not substitute a higher combined
natural/focus score for natural-source accuracy.

## Data and source-family audit

Snapshot: `5af4d189866e41be83ee5c18607226f92f7eace79cb9e0d8c600f73314a2c7f1`. 1,810 input records,
308 exact duplicate records merged, 1
cross-family copy record excluded, 1,501 retained.
All 208 final assignments are frozen before windows. Exact/lexical/normalized
copy auditing is unchanged. All 192 initial families retain their assignments;
the literal revision extends the map to 208. Golden and Playground are excluded.
Original source, complete licenses, hashes, snapshots and every run remain external
under `~/Datasets/neural-semantic-highlighting/rust` and `artifacts/rust`.

Capture pins 41 Serde, 60 Tokio and 60 Regex source files at immutable commits;
`dataset/upstreams.json` retains Git blobs and licenses. The shared collector
excludes reserved `runtime` directory paths, leaving 146 eligible natural files.
All 1,810 collected natural/original-focus records pass the pinned grammar and
coverage checks: zero quarantines in this bounded capture, not a claim that all
Rust syntax is supported. The initial 1,152 authored tasks cover 48 intact families;
512 additional literal/context tasks cover 16 families. Duplicate variants stay
in their family and do not cross splits.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          114 |       1072 |    2641 |
| validation |           15 |        154 |     346 |
| test       |           15 |        131 |     323 |

## Environment and training

The user-authorized update changed the existing stable compiler from Rust 1.97.1
into **Rust/Cargo 1.99.1**, with rustup 1.29.3. Six authored metadata-only compiler
checks cover common 2018/2021/2024 source, C strings on 2021/2024, and modern 2024
let chains/unsafe attributes/externs. All eight displayed sources also pass
`rustc --edition=2024 --emit=metadata` using only the standard library. Compiler
identity, commands, source hashes and original authored probes are recorded in
`reports/toolchain.json`. No collected project builds or runs; no Cargo dependency,
nightly toolchain, global library or extra SDK is installed.

Offline Gold uses pinned Tree-sitter 0.25.10 / Rust grammar 0.24.2, built with
existing Apple Clang into project cache. This is parse-only CST/source-local
supervision, not rustc type-checker labels. Unsupported grammar, hidden/unmapped
macro separators and incomplete coverage fail closed. No project config, module,
build script, dependency or procedural macro executes during labeling.

The model has **894,743 parameters**, four layers, width 128, four heads,
FFN 512 and **512 original UTF-8 bytes** of context. It transfers the compatible
full C++ checkpoint `artifacts/cpp/context512-mixed-v2-20261109-01/candidates/epoch-0002.pt`,
never inference `.pt`/ONNX. A smoke check precedes 3 + 6 short initial epochs.
The literal revision transfers the preserved full initial epoch-9 checkpoint,
with a fresh optimizer, learning rate 0.00015 and focus batch size 32; it runs
3 + 3 bounded epochs. Continuation retains full optimizer/RNG state. Measured
epoch/checkpoint times are in `reports/experiments.json`; full checkpoints and
invocations stay in ignored runs. Epochs took roughly 18–23 seconds on this host.

## Visible development review

Eight independent, compiler-checked display examples aggregate
92.27% exact-span F1. This is development evidence,
not an unseen score. Ten natural validation files were also read directly;
their displayed base F1 ranges from 88.05% to 98.48%.

| Display example    | Exact-span F1 |
| ------------------ | ------------: |
| async.rs           |        97.17% |
| edition2024.rs     |        89.23% |
| hello.rs           |        90.99% |
| macros.rs          |        92.61% |
| ownership.rs       |        98.47% |
| patterns.rs        |        90.45% |
| raw-strings.rs     |        74.07% |
| traits-generics.rs |        95.08% |

The neural model exactly matches all spans/roles/modifiers in 7/23
Golden cases. The offline teacher separately passes all 23 independent
marked cases and eight teacher tests. Missing/unexpected spans and modifier
metrics remain in `reports/`. Raw/format strings are still weaker (74.07% in
the mixed literal example); the bounded refinement is retained without claiming
perfect literal recognition. Local symbol roles, macro DSL names, attributes,
patterns and const generics have measured residual errors.

Browser conversion/parity tests consistency with this selected model, not perfect
semantics. Runtime consumes only original text and learned weights, without SDK,
Cargo, parser, macro expansion, Gold cuts, source-regex repair or code execution.
