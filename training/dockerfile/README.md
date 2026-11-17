# Dockerfile training

Use the existing four-layer width-128, four-head, FFN-512 byte Transformer with
512 original UTF-8 bytes of context. The twelve-role/two-modifier schema has
893,969 neural parameters. Initialize compatible weights from the preserved full
Bash artifacts checkpoint, not an exported inference model. Its optimizer/RNG,
all old data and formal weights remain preserved; the Dockerfile run is fresh.

    make dataset-dockerfile
    make test-labeling-dockerfile
    caffeinate -i make train-dockerfile-smoke DOCKERFILE_DEVICE=mps DOCKERFILE_RUN=artifacts/dockerfile/smoke-20261117-01 DOCKERFILE_INIT_FROM=artifacts/bash/context512-heredoc-fragments-20261108-01/candidates/epoch-0020.pt
    caffeinate -i make train-dockerfile DOCKERFILE_DEVICE=mps DOCKERFILE_EPOCHS=3 DOCKERFILE_RUN=artifacts/dockerfile/context512-20261117-01 DOCKERFILE_INIT_FROM=artifacts/bash/context512-heredoc-fragments-20261108-01/candidates/epoch-0020.pt
    caffeinate -i make continue-dockerfile DOCKERFILE_DEVICE=mps DOCKERFILE_EPOCHS=3 DOCKERFILE_CHECKPOINT=artifacts/dockerfile/context512-20261117-01/last.pt

Natural documents are fully presented each epoch; bounded independently authored
focus windows rotate separately. Start with smoke and short stages, measure
actual epoch time, then review natural validation, marked Golden and eight real
consumer displays. Archive full candidates before continuation. Select/freeze
before the first adaptive test; do not train further on an exposed test cohort.
Keep natural, focus, visible and composed metrics separate. No parser, regex,
source-spelling repair, Docker service or child-language runtime is added to
inference. The standalone model learns the offline Shell/JSON role supervision.

    make evaluate-dockerfile DOCKERFILE_CHECKPOINT=artifacts/dockerfile/RUN/candidates/SELECTED.pt
    make challenge-dockerfile DOCKERFILE_CHECKPOINT=artifacts/dockerfile/RUN/candidates/SELECTED.pt
    make export-dockerfile-model DOCKERFILE_CHECKPOINT=artifacts/dockerfile/RUN/candidates/SELECTED.pt DOCKERFILE_TEST_REPORT=artifacts/dockerfile/RUN/test.json

Retain matching held-out evidence and model documentation before export. Verify
native/ONNX numerics, full browser/native original-source parity, an independent
private-tarball consumer, themes/custom CSS and the complete `make check` suite.
Keep the repository/packages private; commit short English stages, publish only
when explicitly authorized. No language SDK or Docker installation is required.

A fresh experiment may use `--loss-weight-stream natural` to fit class balance
on real training windows, while retaining bounded curriculum presentations. This
prevents long authored bodies from over-weighting rare image-name roles; default
behavior for all earlier packs stays unchanged. Resume preserves the chosen
weights/configuration. The optional `training.dockerfile.calibrate` command is a
validation-only joint BIO diagnostic; it was not selected because the small
validation gain regressed visible Unicode regions. Canonical greedy inference
uses only the existing touching-string policy, without inspecting spelling.
Protocol changes start a new bound run; preserve old configs/checkpoints rather
than rewriting provenance. The v2 prepared reference bytes are all unchanged.
