# Protocol Buffers training

Use the shared four-layer width-128, four-head, FFN-512 byte Transformer with
512-byte context and the existing learned local residual. Compatible weights
initialize from a full selected GraphQL artifacts checkpoint, never inference
`packs/*/model/model.pt`. Optimizer/RNG start fresh; old experiments/data/weights
remain intact. Each epoch covers natural windows plus rotating bounded original
focus windows. Smoke first, then short stages and actual validation review.

    make dataset-protobuf
    make test-labeling-protobuf
    caffeinate -i make train-protobuf-smoke PROTOBUF_DEVICE=mps PROTOBUF_LOCAL_KERNEL=5 PROTOBUF_RUN=artifacts/protobuf/smoke-20261119-01 PROTOBUF_INIT_FROM=artifacts/graphql/context512-20261119-03/candidates/epoch-0010-best.pt
    caffeinate -i make train-protobuf PROTOBUF_DEVICE=mps PROTOBUF_EPOCHS=3 PROTOBUF_LOCAL_KERNEL=5 PROTOBUF_RUN=artifacts/protobuf/context512-20261119-01 PROTOBUF_INIT_FROM=artifacts/graphql/context512-20261119-03/candidates/epoch-0010-best.pt
    caffeinate -i make continue-protobuf PROTOBUF_DEVICE=mps PROTOBUF_EPOCHS=3 PROTOBUF_CHECKPOINT=artifacts/protobuf/context512-20261119-01/last.pt

Record actual epoch times. Inspect real natural validation errors, independent
Golden and visible source. Freeze a complete candidate and validation-only
selection before the first independent adaptive test; never train/select from
that test. Keep natural/focus/display/Golden numbers distinct. Formal export
requires matching test evidence and reviewed model documentation.

    make evaluate-protobuf PROTOBUF_CHECKPOINT=artifacts/protobuf/RUN/candidates/SELECTED.pt
    make challenge-protobuf PROTOBUF_CHECKPOINT=artifacts/protobuf/RUN/candidates/SELECTED.pt
    make export-protobuf-model PROTOBUF_CHECKPOINT=artifacts/protobuf/RUN/candidates/SELECTED.pt PROTOBUF_TEST_REPORT=artifacts/protobuf/test-final.json

Verify native/ONNX numeric preservation, browser parity across all packs, an
independent private-tarball consumer, themes/custom CSS and repository checks.
No protoc/new SDK/global dependency is installed; parsing is offline supervision
only, without runtime regex/CST/spelling fallback. Retain short English stage
commits; publication and pushes require the user's applicable instruction.
