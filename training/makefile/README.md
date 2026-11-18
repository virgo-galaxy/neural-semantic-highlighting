# Makefile training

Use the established four-layer width-128, four-head, FFN-512 byte Transformer,
with 512 original UTF-8 bytes of context. Its ten-role/two-modifier schema learns
Make plus common recipe Shell supervision in one standalone model. Initialize
compatible weights from a full `artifacts` checkpoint, never a `packs` inference
model. Initialization starts a fresh optimizer/RNG; resume uses the run's last.pt.

    make dataset-makefile
    make test-labeling-makefile
    caffeinate -i make train-makefile-smoke MAKEFILE_DEVICE=mps MAKEFILE_RUN=artifacts/makefile/smoke-20261118-01 MAKEFILE_INIT_FROM=artifacts/dockerfile/context512-canonical-20261117-01/candidates/epoch-0001.pt
    caffeinate -i make train-makefile MAKEFILE_DEVICE=mps MAKEFILE_EPOCHS=3 MAKEFILE_RUN=artifacts/makefile/context512-20261118-01 MAKEFILE_INIT_FROM=artifacts/dockerfile/context512-canonical-20261117-01/candidates/epoch-0001.pt
    caffeinate -i make continue-makefile MAKEFILE_DEVICE=mps MAKEFILE_EPOCHS=3 MAKEFILE_CHECKPOINT=artifacts/makefile/context512-20261118-01/last.pt

Every epoch presents natural windows and rotates bounded focus tasks. Start with
smoke/short stages, measure actual time, archive full candidates, inspect natural
validation and original displays. Fresh experiments can choose natural-only
class weights; resume retains the stored training configuration. Select/freeze
before the first independent adaptive test; never tune against exposed test data.
Keep real-source, focus, Golden and display metrics separate. Parser acceptance
and browser parity do not certify complete semantic accuracy.

    make evaluate-makefile MAKEFILE_CHECKPOINT=artifacts/makefile/RUN/candidates/SELECTED.pt
    make challenge-makefile MAKEFILE_CHECKPOINT=artifacts/makefile/RUN/candidates/SELECTED.pt
    python -m training.makefile.review --checkpoint artifacts/makefile/RUN/candidates/SELECTED.pt --output artifacts/makefile/review.json
    make export-makefile-model MAKEFILE_CHECKPOINT=artifacts/makefile/RUN/candidates/SELECTED.pt MAKEFILE_TEST_REPORT=artifacts/makefile/RUN/test.json

Retain matching test/checkpoint/configuration/semantic evidence before native and
ONNX export. Verify numerics at eight lengths, all prior browser/native cases,
an independent private-tarball consumer, themes/custom CSS and `make check`.
No runtime parser, regex/spelling repair, Make execution or child Shell model is
added. Keep data/history and repository/packages private; use short English
stage commits and publish/push only when explicitly requested.

The reviewed refinement uses a fresh configuration-bound run after correcting
adjacent assignment supervision and adding structurally separate original tasks.
Initialize its compatible weights from a preserved complete Makefile candidate;
use `MAKEFILE_LOSS_WEIGHT_STREAM=natural MAKEFILE_LEARNING_RATE=0.00015` for that
fresh experiment. An earlier mixed task revision is rejected by existing
structural-copy exclusion and remains retained; the later revision changes real
rule structure instead of bypassing that safeguard. No independent test result
participates in any correction, task generation or epoch selection.

## Bounded optimization

Preserve the selected baseline and all full checkpoints. The optimization run
initializes from `artifacts/makefile/context512-structures-20261118-01/candidates/epoch-0012-best.pt`,
with a new immutable snapshot and fresh optimizer. Keep the same four-layer,
width-128, context-512 backbone; `MAKEFILE_LOCAL_KERNEL=5` optionally enables the
existing zero-initialized five-byte depthwise residual (768 extra parameters).
Start with three/six epochs, `MAKEFILE_FOCUS_BATCH_SIZE=16`, natural class weights
and learning rate 0.0001. No source parser/spelling rule is added to inference.

`python -m training.makefile.calibrate --checkpoint FULL.pt --output CALIBRATED.pt`
fits existing legal BIO/role transitions on natural **train** Gold only. A fixed
20-point grid selects the maximum minimum original exact-span F1 of all, fresh
and legacy **validation** cohorts. Every matrix/weight/report is bound to its
source checkpoint and frozen protocol. Compare real-code/Golden/displays before
selection. The first new independent test follows all training/calibration;
report its 16 fresh documents separately from the exposed 17-file legacy cohort.

For comparison on validation cohorts of unequal baseline difficulty, pass
`--baseline-validation artifacts/makefile/optimization-20261118/baseline-validation.json`.
The command verifies identical natural validation identities and maximizes the
minimum F1 **gain** on all/fresh/legacy cohorts, retaining absolute metrics. The
initial 12-point grid, its boundary-selected expansion and the prior absolute
selection trials remain retained. All choices precede reading fresh test results.
