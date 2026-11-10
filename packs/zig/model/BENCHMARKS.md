# Zig 0.17.1 baseline evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match.
Role macro F1 averages represented roles; declaration modifiers are separate.
This measures bounded syntax/source-local roles, not project type checking,
comptime evaluation, dependency resolution or API compatibility certification.
Only **Zig 0.17.1** is targeted; historical releases and master are excluded.

| Evidence           | Documents | Exact-span F1 | Role macro F1 |
| ------------------ | --------: | ------------: | ------------: |
| Natural validation |        12 |        94.64% |        80.13% |
| Focus validation   |        80 |        98.10% |        96.96% |
| First natural test |        21 |        92.51% |        73.75% |
| First focus test   |        80 |        96.90% |        86.64% |

Frozen full candidate: `artifacts/zig/context512-contextual-20261110-01/candidates/epoch-0006.pt`, epoch 6 of the contextual-call
revision. Fixed natural validation role macro F1
(0.7796) selects within that run. Natural validation
source, independent Golden and eight displayed examples were reviewed before
freeze and the first adaptive test. No training followed that test. Combined
natural/focus quality is not substituted for natural-source quality.

## Current-source capture and audit

Snapshot: `d1fbf4ea68adfec484342a7ad51e1697d5dabf288056c52ecb8de182710e596a`. 1,168 input records,
168 exact duplicate records merged,
0 cross-family copies excluded,
1,000 retained. All 77 source/module/task family
assignments were frozen before initial training and remain unchanged through
the Gold correction. Exact/lexical/normalized copy auditing precedes windowing.

Only the SHA-256-pinned official 0.17.1 release archive is captured: 96 bounded
standard-library and 64 compiler files, with complete original MIT license.
The 1,008 authored records cover 42 intact task families. All 1,168 records pass
the current official source checks and complete original-text coverage: zero
quarantines in this bounded capture, not a universal syntax claim. Golden and
Playground source are excluded. The natural validation set is small and dominated
by std crypto plus HTTP source; the test uses different intact module families.
This single upstream is not representative evidence for every Zig application.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          127 |        680 |    2463 |
| validation |           12 |         80 |     301 |
| test       |           21 |         80 |     303 |

Original source, licenses, Gold revisions, immutable snapshots and complete runs
remain under `~/Datasets/neural-semantic-highlighting/zig` and `artifacts/zig`.
The initial snapshot and all earlier language artifacts are preserved.

## Toolchain and supervision

The user-authorized upgrade changed the existing host Zig from 0.14.1 to
**0.17.1**. Homebrew is now 7.0.13; required LLVM/LLD 22.1.8, xz/zstd and portable
Ruby dependencies accompanied that update. LLVM postinstall was repaired and
completed; the old Zig keg remains. One upgrade test, all 42 authored template
family representatives (`zig test`) and all eight displayed sources
(`zig build-exe -fno-emit-bin`) pass this SDK. Current I/O, reflection field names,
allocator operations and errdefer syntax are checked against this exact release.
Commands, original authored sources and hashes are in `reports/toolchain.json`.
Collected projects never compile, import dependencies or execute.

Offline Gold uses this SDK's official `std.zig.Ast`, `Tokenizer`, primitive
metadata and source-only `zig ast-check`, with SDK/helper/compiler/binary hashes
in `reports/teacher-tools.json`. The helper only parses; source validation does
not evaluate comptime, follow imports, embed files or perform target/type checks.
Nine independent teacher tests include deliberately missing imports/files and a
comptime compile-error to verify no evaluation. Old builtin/async syntax is
rejected. This is source-local supervision, not whole-project compiler semantics.
The review corrected called contextual-dot names such as `.init()`/`.stdout()`
from enum-member to function; the same source families were relabeled without
recollecting or adding visible examples to training.

## Model and bounded training

**894,485 parameters**, four layers, width 128, four heads, FFN 512,
**512 original UTF-8 bytes** of context. The initial smoke/full run transfers the
compatible full Rust checkpoint
`artifacts/rust/context512-literals-20261110-01/candidates/epoch-0004.pt`.
The initial phase runs three epochs. The Gold correction transfers its preserved
full epoch-3 checkpoint with a fresh optimizer, then runs three plus three short
epochs. Continuation retains optimizer/RNG state; selected epoch need not be the
last one. Measured times/invocations are retained in `reports/experiments.json`
and ignored full runs. No inference `.pt` or ONNX is a training initializer.

## Visible development review

Eight independent SDK-checked display examples aggregate
97.26% exact-span F1. Ten real validation sources were
read directly, with base F1 from 91.61% to 98.37%. These are
development diagnostics, not unseen scores.

| Display example      | Exact-span F1 |
| -------------------- | ------------: |
| captures.zig         |        99.40% |
| comptime.zig         |        97.66% |
| containers.zig       |        96.00% |
| errors-optionals.zig |        96.83% |
| hello.zig            |        95.83% |
| memory.zig           |       100.00% |
| reflection.zig       |        96.08% |
| strings.zig          |        93.10% |

Neural spans/roles/modifiers are completely exact in 10/23 Golden
cases; the separate offline teacher passes all 23 manually marked
cases and nine tests. Missing/unexpected spans remain in the reports. The mixed
string/quoted-identifier example remains weaker at 93.10%; local name
roles, inferred types, captures and declaration flags retain controlled errors.
Browser conversion/parity verifies consistency with these weights, not perfect
semantics. Runtime uses no Zig compiler, parser, Gold cuts, source-regex repair,
imports or comptime evaluation.

The full-check pass caught an undeclared `Thing` in the new contextual-call
Golden fixture. Its generic type declaration was added after first test; the
fixture was rechecked against the official teacher and frozen neural model.
All 23 marked cases and nine teacher tests then pass; neural exactness is
10/23 with the corrected fixture. No training, source corpus, dataset assignment
or model weights changed.
