# Diff/Patch training

Use the shared four-layer width-128, four-head, FFN-512 byte Transformer and
512-byte context. Compatible full Markdown artifacts weights initialize a fresh
run, with the existing zero-initialized five-byte local residual. Never train
from `packs/*/model/model.pt` or ONNX. Preserve all older data and experiments.
Each epoch covers real natural windows plus rotating bounded original focus.

    make dataset-diff
    make test-labeling-diff
    caffeinate -i make train-diff-smoke DIFF_DEVICE=mps DIFF_LOCAL_KERNEL=5 DIFF_RUN=artifacts/diff/smoke-20261119-01 DIFF_INIT_FROM=artifacts/markdown/optimization-20261116/calibrated-fences-e3.pt
    caffeinate -i make train-diff DIFF_DEVICE=mps DIFF_EPOCHS=3 DIFF_LOCAL_KERNEL=5 DIFF_RUN=artifacts/diff/context512-20261119-01 DIFF_INIT_FROM=artifacts/markdown/optimization-20261116/calibrated-fences-e3.pt
    caffeinate -i make continue-diff DIFF_DEVICE=mps DIFF_EPOCHS=3 DIFF_CHECKPOINT=artifacts/diff/context512-20261119-01/last.pt

Measure actual epoch time and review real natural validation plus independent
Golden and visible patches at short stages. Freeze the full candidate and
validation-only decision before first independent adaptive test. Do not fit or
choose from exposed test results. Keep natural, focus and visible scores separate.

    make evaluate-diff DIFF_CHECKPOINT=artifacts/diff/RUN/candidates/SELECTED.pt
    make challenge-diff DIFF_CHECKPOINT=artifacts/diff/RUN/candidates/SELECTED.pt
    make export-diff-model DIFF_CHECKPOINT=artifacts/diff/RUN/candidates/SELECTED.pt DIFF_TEST_REPORT=artifacts/diff/test-final.json

Formal export requires matching independent evidence and reviewed model docs.
Verify float32 native/ONNX conversion, full browser parity, private-tarball public
imports, one-model assets, addition/deletion colors, all six theme/mode pairs,
custom CSS, source preservation and repository checks. No runtime Git/parser/
regex/prefix repair or embedded-language guessing is introduced. Keep short
English stage commits and the private distribution policy.
