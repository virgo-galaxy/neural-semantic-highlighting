# C baseline evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match.
Role macro F1 averages represented roles; declaration modifiers are scored
separately. This is source-local grammar supervision, not a compiler/type checker.
Natural source, focus tasks and visible development probes are separate evidence.

| Evidence           | Documents | Exact-span F1 | Role macro F1 |
| ------------------ | --------: | ------------: | ------------: |
| Natural validation |        21 |        94.21% |        81.90% |
| Focus validation   |        96 |        97.33% |        94.19% |
| First natural test |        18 |        93.90% |        87.23% |
| First focus test   |       144 |        95.35% |        91.41% |

Selected full checkpoint: `artifacts/c/context512-mixed-20261109-01/candidates/epoch-0002.pt`, epoch 2.
Selection maximized natural fixed-validation role macro F1
(0.8678). Real validation source and visible probes
were reviewed before the first adaptive test. No training followed first test
inspection; that test is now known evidence for future comparisons.

## Data and protocol

Immutable snapshot: `f2b310c82ecc7c488cd205659d4772c8ab4a1f51e5db2f51f2d85d4f5e29aa10`.
1,488 input records; 0 exact duplicate records merged;
0 cross-family copy records excluded; 1,488 retained.
Source/task families are frozen before training, with exact, lexical and normalized
copy auditing before grouped windows. `.c` and `.h` sharing a module basename stay
in one family. Golden and Playground never enter collection roots.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          153 |       1056 |    2470 |
| validation |           21 |         96 |     249 |
| test       |           18 |        144 |     291 |

The bounded capture has 90 curl 8.13.0, 90 Git 2.49.0 and 50 Redis 7.4.2 original
source/header files. Exact revisions and per-file Git blobs are in `upstreams.json`.
Full licenses, original source bytes and hashes remain external. 38 captured files
outside the pinned grammar were quarantined with exact source/error identities;
none was relabeled with a fallback parser. 1,008 original focused tasks cover 42
families of functions, pointers, macros, structs, callbacks and related syntax.
The targeted revision adds 288 independent multiline tasks across 12 families.
All 224 original family assignments were preserved and extended to 236 before
that revision trained. All data revisions and previous experiments are retained.

The existing Apple Clang 21 / macOS Command Line Tools SDK successfully compiled
and ran authored C11/C17/C23 probes. It builds only the pinned Tree-sitter 0.25.10 /
C grammar 0.24.1 offline parse library; no compiler/SDK/global package was installed.
Collected projects never run, headers are not followed and macros are not expanded.
The source parser and macro replacement scanner are offline supervision tools only.

## Visible code review

Ten natural validation files across lengths and upstreams, eight independently
authored display files and 18 manually marked Golden cases were reviewed.
These visible probes guide development; their scores are not independent test scores.

| Display probe | Exact-span F1 |
| ------------- | ------------: |
| callbacks.c   |        98.68% |
| file-reader.c |        98.28% |
| hello.c       |        95.89% |
| linked-list.c |        94.12% |
| literals.c    |        92.63% |
| macros.h      |        95.81% |
| modern-c.c    |        94.52% |
| points.c      |       100.00% |

Neural Golden matched all spans and modifiers exactly in 11/18 cases.
The teacher separately passes all 18 expected cases. Detailed missing/unexpected
spans and full source are retained in `reports/`.

## Training and inference

Architecture is unchanged: 894,227 parameters, four layers, width 128,
four attention heads, FFN 512 and 512 original UTF-8 bytes per window.
The first full experiment started with explicit compatible weights-only transfer
from the full selected C# training checkpoint in `artifacts/csharp`, then ran three
initial and six bounded continuation epochs. Timing and optimizer/RNG state remain
in the run logs. Inference-only `.pt` or ONNX files were never used for training.
The best complete first-run candidate was epoch 7. The mixed-data experiment
initialized from that full checkpoint and ran three epochs at learning rate
0.0001; epoch 2 won fixed natural validation selection. Measured epochs took
about 17–21 seconds on this host. No training followed the first independent test.

Adaptive inference sees only predicted boundaries and original text, not Gold cuts,
regex correction, a compiler, SDK or grammar. Long code uses multiple windows;
long comments/macros/strings and distant declarations remain bounded-context limits.
Float32 native and browser exports preserve selected tensors exactly. Browser
numerical checks and real end-to-end spans are recorded separately.
