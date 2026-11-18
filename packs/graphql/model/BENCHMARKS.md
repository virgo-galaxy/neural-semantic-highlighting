# GraphQL baseline evaluation

Exact-span F1 requires identical original UTF-16 start, end and role. Modifiers
are scored separately. Natural, authored focus and visible evidence are distinct;
these small family holdouts do not establish uniform feature/project accuracy.

| Evidence               | Stream  | Documents | Exact-span F1 | Role macro F1 | F1 with modifiers |
| ---------------------- | ------- | --------: | ------------: | ------------: | ----------------: |
| Validation             | natural |        18 |        97.63% |        80.79% |            95.70% |
| Validation             | focus   |        80 |        94.84% |        94.54% |            91.38% |
| First independent test | natural |        14 |        96.36% |        93.08% |            89.82% |
| First independent test | focus   |        80 |        96.36% |        86.81% |            93.32% |

The primary result is **96.36% on 14 first independent natural
files**. Visible displays aggregate 97.60%;
the Unicode block-string example remains 80%. Strict marked Golden is
10/24 whole cases exact including modifiers,
with 92.52% base-span F1. No Golden/display
source enters training or the independent test.

## Frozen data and bounded training

49 commit/blob-pinned original files across five application/library repositories
are captured with their applicable original licenses. Whole directory/application
families are fixed on metadata before reading source or predictions. There are
800 original focus tasks in 40 structural families. The unchanged shared exact,
lexical and shape exclusion removes cross-family copies; no split rule is weakened.

| Split      | Natural documents | Focus tasks | Windows |
| ---------- | ----------------: | ----------: | ------: |
| train      |                15 |         600 |     801 |
| validation |                18 |          80 |     114 |
| test       |                14 |          80 |     102 |

Final snapshot `56ea1170250b7974d75bb815b499cc015280d8a9f7830ee29f8a8038fdf5c924`; manifest SHA-256
`a8c7cfbdfbd2c85d4782df4f1195266619cfbf7ca686c65aa2ef9fcbf9a0c91f`. All original corpora, Gold, earlier snapshots,
full optimizer/RNG checkpoints and rejected experiments remain outside Git.
The first exploratory run precedes metadata formatting; subsequent fresh runs
use the republished immutable provenance. Original source content is retained.

Four layers, width 128, four heads, FFN 512 and 512-byte context contain
**895,124 parameters**, including the existing five-byte local
residual. Compatible weights initialize from the preserved full Makefile
artifacts checkpoint, followed by fresh GraphQL stages; no inference artifact is
used for training. Three short stages complete 36 non-smoke epochs in
117.1 seconds. Smoke verifies reload/inference first. Exact invocations,
validation histories and times are retained in [experiments](reports/experiments.json).

The selected full checkpoint is `artifacts/graphql/context512-20261119-03/candidates/epoch-0010-best.pt`, epoch 10,
SHA-256 `38695bf08512023e5275bac081b94de83ffc5f0deaff219264298f411d364a59`. Highest final-run fixed natural validation role
macro F1 selects the epoch, followed by actual adaptive validation and visible
review. A train-fitted joint decoder is retained as a rejected diagnostic:
its validation macro gain suppressed enum values and regressed visible Schema.
The selected greedy policy only coalesces touching equal-role strings/comments;
no parser, regex, source-spelling repair or type resolver runs during inference.

[Freeze](reports/selection.json) precedes first independent test. No subsequent
training or decoder choice uses that test. Export binds model, schema, semantic
contract, pack policy, dataset and matching independent test evidence. ONNX
conversion preserves float32 weights without quantization or retraining.

## Offline oracle and review

Pinned graphql-core 3.3.2 (GraphQL.js 17.1.0 port) supplies parse-only AST and
original lexical ranges. Its verified wheel source is extracted under ignored
artifacts, without pip/global dependency or SDK installation. It never validates
against an external schema, resolves imports or executes operations/resolvers.
24 independent hand-marked cases and five teacher tests pass. Original comments,
strings/escapes, BOM, CRLF and UTF-16 ranges remain unchanged. Schema-local roles,
not global symbol resolution, define labels. Reports retain all visible errors
and inspected actual validation files. Browser parity is runtime evidence, not
additional accuracy. Sources and licenses remain external and private.
