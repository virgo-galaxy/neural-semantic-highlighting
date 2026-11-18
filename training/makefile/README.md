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
