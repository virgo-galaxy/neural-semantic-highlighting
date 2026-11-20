# JS / TS quality evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match.
Modifier scores are separate in the raw reports.

| Evidence                                  | Files | Previous | Selected F1 | Selected role macro |
| ----------------------------------------- | ----: | -------: | ----------: | ------------------: |
| Legacy natural test (exposed)             |    50 |   99.31% |      99.45% |              98.57% |
| New authored context holdout              |   384 |   89.82% |      97.94% |              94.79% |
| 24 real Virgo Design TSX files, read-only |    24 |   99.28% |      99.39% |              98.71% |

The existing 160-case RegExp development challenge improves from 61.33% to
93.27% exact-RegExp F1 (104 TP, 14 FP, one FN). Negative clean cases are 54/60,
compared with 59/60 previously, so recall gains do not imply perfect precision.
The separate first-read authored holdout has **96.48% RegExp F1** and 97.94%
overall F1. Its 384 files and the 24 product files were conservatively checked
against natural training and every authored TRAIN version using exact text and
normalized AST-kind structure; none overlapped. These are bounded development
contexts and a product snapshot, not universal language accuracy.

The paired RegExp challenge is exact on 40 isolated and 40 contextual cases;
all 162 JSX/TSX marked assertions pass. Natural test string F1 improves from
96.82% to 97.51%, comment F1 from 91.73% to 91.98%. In the small real-product
cohort, comment F1 decreases from 100% to 91.67%; keep that regression visible.

## Selection and reproducibility

A zero-initialized five-byte depthwise residual learns local byte context.
Bounded transfers use full checkpoints, 300 deterministic natural TRAIN replay
documents, compiler-labelled authored contexts, EOF/newline/semicolon coverage
and a recorded source-end loss weight. Natural validation micro/macro guards
constrain focused selection. No newline insertion, parser, RegExp coalescing or
source-spelling repair is used at runtime. Context remains 512 original UTF-8
bytes. The later negative-heavy run did not beat validation and was rejected.

Selected full checkpoint: `artifacts/quality-20261119/typescript/tail-reviewed.pt`. Parameters: **897,833**. Full source/RNG/optimizer experiments and all external data remain intact.

Historical evidence is preserved in [the preceding bundle](../model-20261119-v1/BENCHMARKS.md).
