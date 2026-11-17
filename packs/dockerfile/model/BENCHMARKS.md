# Dockerfile baseline evaluation

Exact-span F1 requires identical original UTF-16 start, end and role; modifiers
are separate. This is source-local display quality, not complete image/platform,
build, shell-runtime or environment correctness. Natural, authored and visible
results remain separate; no combined/focus score substitutes for real accuracy.

| Evidence               | Stream  | Documents | Exact-span F1 | Role macro F1 | F1 with modifiers |
| ---------------------- | ------- | --------: | ------------: | ------------: | ----------------: |
| Validation             | natural |        12 |        88.00% |        87.84% |            86.82% |
| Validation             | focus   |        72 |        96.30% |        95.91% |            96.25% |
| First independent test | natural |        14 |        96.33% |        95.62% |            96.06% |
| First independent test | focus   |       120 |        91.96% |        90.19% |            91.84% |

The primary result is **96.33% across 14 first independent
real documents**. Validation remains lower at 88.00%
on 12 different documents. These small, bounded family holdouts do not establish
uniform accuracy across all projects or Dockerfile features.

## Frozen sources and training

70 bounded original filename candidates reuse 15 existing public Git tree
inventories/revisions; Git blobs, original bytes and applicable licenses are
retained. One candidate is a JavaScript highlighter module and is quarantined,
not silently relabeled. Two exact duplicates merge and two cross-family copies
are excluded. All natural related-family assignments are fixed before parsing
or predictions. Golden and Playground never enter collection roots.

24 original structural families / 576 tasks are followed by a bounded 12-family /
288-task mixed extension after actual validation/display review. It addresses
literal paths versus image/stage names, USER names, shell option values and
BOM/CRLF/Unicode/markup/instruction-looking opaque bodies. All 83 prior
assignments and original natural records remain unchanged; 95 families are
frozen in the final map. Every corpus, Gold, prepared revision and trial remains
retained outside Git. Final prepared snapshot:
`0844cc2a8d7af15a0d435b3c39701c66d812c99690d84c03c2786fb6db8e15bf`; manifest hash `f339732daef2b514f47669c449baf9313053fa394afde8034cebe76c5e5fcdb9`.

| Split      | Natural documents | Authored focus | Windows |
| ---------- | ----------------: | -------------: | ------: |
| train      |                39 |            672 |    2743 |
| validation |                12 |             72 |     377 |
| test       |                14 |            120 |     513 |

The model has **893,969 parameters**, four layers, width 128, four attention
heads, FFN 512 and **512 original UTF-8 bytes** of context. Compatible weights
start from the preserved full Bash checkpoint
`artifacts/bash/context512-heredoc-fragments-20261108-01/candidates/epoch-0020.pt`.
Its optimizer/RNG and all previous inference models remain untouched.
A smoke reload/inference check precedes short bounded stages. Exact invocations,
early stopping and timings are [retained](reports/experiments.json): all
**51 non-smoke epochs take 177.3 seconds**; no training follows the first
independent test. Fresh real-source class balancing prevents long authored
bodies from skewing the image-name weight; other packs retain their defaults.

The canonical protocol uses the existing source-blind union of touching string
spans with identical modifiers. No whitespace gap, role or source spelling is
changed. The [audit](reports/protocol-v2-audit.json) proves **all prepared original
source/reference/label/window bytes are unchanged** from the preceding protocol;
old configs/checkpoints remain archived. A new bound experiment follows the
policy change. Joint BIO decoding was tried on validation only but not selected
because its small score gain regressed visible Unicode. The final decoder is
canonical greedy, without a runtime parser, regex or source-spelling repair.

Selected full checkpoint: `artifacts/dockerfile/context512-canonical-20261117-01/candidates/epoch-0001.pt`, epoch 1,
SHA-256 `1346dfa64f159568ac2410ff1fd97a82813b8bd8614452b0624dcceeda99d116`. Highest fixed natural validation role macro F1
within the canonical run selects the epoch. Actual display and natural validation
review precede [freeze](reports/selection.json) and the first independent adaptive
test. The export binds checkpoint/schema/semantic/configuration identity and test
evidence. Browser conversion preserves selected weights without quantization.

## Offline oracle and actual review

The independent structural oracle is **official BuildKit v0.35.0**, compiled
with existing Go 1.27.1 in isolated project caches, automatic SDK download
disabled. Module checksums, Go dependency lock, compiler/helper hashes and
original licenses remain retained. Existing pinned Shell and JSON assets supply
nested supervision. No Docker Engine, new language SDK or global dependency is
installed; no collected command, image, source or dependency executes. AST
acceptance is not complete Docker build validation.

The teacher passes **42 independently hand-marked cases and 12 tests**. The
selected neural model has **23/42** whole cases exact including modifiers,
with **85.41%** base-span F1. These
strict visible edge probes remain separate from independent natural accuracy.
Eight authored displays aggregate **96.62%**.
English and Unicode opaque heredoc reference bodies are **2/2 exact**; exec,
heredoc and variables displays are exact at base-span level. The Unicode display
still misclassifies its opening comment (95.00% F1). Ten real natural validation
sources were inspected before freeze; their explicit missing/unexpected ranges
remain in [real-code review](reports/real-code.json).

Detailed first-test counts are in [test metrics](reports/test-metrics.json).
Browser/native parity and independent package checks establish consistent
original-text/span behavior, not semantic perfection. See [known limits](KNOWN_ISSUES.md).
