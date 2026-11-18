# Makefile baseline evaluation

Exact-span F1 requires identical original UTF-16 start/end and role; modifiers
are separate. This measures source display roles, not a correct build, expansion,
resolved dependency graph or complete platform/shell behavior. The primary result
is **89.14% on 17 independent natural documents**.
Small bounded family cohorts are not a guarantee for every project or construct.

| Evidence               | Stream  | Documents | Exact-span F1 | Role macro F1 | F1 with modifiers |
| ---------------------- | ------- | --------: | ------------: | ------------: | ----------------: |
| Validation             | natural |        11 |        86.94% |        89.51% |            86.19% |
| Validation             | focus   |       120 |        98.30% |        98.79% |            98.23% |
| First independent test | natural |        17 |        89.14% |        88.76% |            88.72% |
| First independent test | focus   |       120 |        98.59% |        99.16% |            98.34% |

## Frozen source evidence

83 bounded filename candidates from 17 existing pinned public projects retain
Git blobs, original bytes and licenses. Complete related-family assignments are
fixed from metadata before parsing/training; 27 unsupported/dialect/false filename
candidates remain quarantined. No file is renamed into a different language.
Natural, authored, Golden and display evidence remain separate.

24 initial structural families / 576 original tasks vary block and binding counts.
Actual natural validation exposes the pinned CST's greedy `NAME?=value`/`NAME+=value`
names, so a checked offline original-adjacency correction creates a new Gold/run
revision before any independent test. All natural bytes/groups remain unchanged;
six documents receive corrected roles. A 12-family mixed-v1 extension is wholly
excluded by the unchanged structural-copy safeguard; it and its intermediate run
remain preserved. Mixed-v2 varies actual rule structure as well as bindings/body
lengths; 12 families / 288 tasks pass the same safeguard. No holdout or exclusion
rule is relaxed. [Revision audit](reports/data-revision-audit.json) retains details.

| Split      | Natural documents | Authored focus | Windows |
| ---------- | ----------------: | -------------: | ------: |
| train      |                28 |            624 |    1619 |
| validation |                11 |            120 |     352 |
| test       |                17 |            120 |     339 |

Selected prepared snapshot: `fff09b03abb21a941795220fcc83c61c01a8a710061407f4c60f08af6ccce661`;
manifest SHA-256 `4101c01ad14ff2b717453040fe2f6cac0b994bb0af8f8933ca8e80360a51f641`. All older source, Gold,
prepared, configuration and checkpoint revisions remain retained.

## Small model and selection

The **893,711-parameter** byte Transformer uses four layers, width 128, four
heads, FFN 512, and 512 original UTF-8 bytes. Compatible weights initialize from
the preserved full Dockerfile artifacts checkpoint, never an inference model.
Later experiments transfer full Makefile candidates with a fresh optimizer/RNG
and bind their own configuration/snapshot. Smoke verifies checkpoint reload and
pure-neural inference. [Experiments](reports/experiments.json) preserve exact
invocations, early stopping, **42 non-smoke epochs / 190.1 seconds**.
Natural windows are fully presented; bounded focus windows rotate separately.

Highest fixed natural validation role macro F1 selects the epoch within each run;
actual natural/visible review precedes [freeze](reports/selection.json). Selected
checkpoint `artifacts/makefile/context512-structures-20261118-01/candidates/epoch-0012-best.pt`, epoch 12, SHA-256
`ed61c5a8c22bf0fc14ad4523c77a9c761cdd11a0df958163a2f9f1b88dd0d273`. No training follows the first independent adaptive test.
Native/browser exports bind checkpoint, test, schema, configuration and semantics;
float32 conversion performs no retraining or quantization.

## Golden, actual code and limits

The offline teacher passes **46 independent hand-marked Golden cases / 12 tests**.
Selected neural whole-case agreement including modifiers is **29/46**,
with **89.69%** base-span F1. Eight visible displays
aggregate **95.54%**. Explicit missing/unexpected spans
from ten actual natural validation files remain in [real-code review](reports/real-code.json).
These visible diagnostics never substitute for independent natural accuracy.

Tree-sitter Make 1.1.1 at pinned commit `5e9e8f8ff3387b0edcaa90f46ddf3629f4cfeb1d`
and runtime 0.25.10 compile with existing Clang in isolated artifacts, with locked
source/binary/compiler/license hashes. Existing Bash/Pygments provides offline
recipe supervision through checked original-coordinate projections. No SDK or
global dependency is installed, and no collected Makefile, recipe, include,
shell/eval/file expansion or dependency executes. [Semantics](../SEMANTICS.md)
describes bounded literal prefix/comment/assignment handling and grammar limits.
Runtime uses one neural model and the existing source-blind touching-string union,
without source parsing, regex, spelling repair or gap bridging.
