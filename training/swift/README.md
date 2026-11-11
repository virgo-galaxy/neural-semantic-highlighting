# Swift training

Reuse the existing four-layer, width-128, 512-byte Transformer and Python/PyTorch
MPS environment. Existing official Swift 6.4.2 supplies offline SwiftParser only;
no language dependency is installed and collected projects are never built/run.

    make dataset-swift
    make test-labeling-swift
    caffeinate -i make train-swift-smoke SWIFT_DEVICE=mps SWIFT_RUN=artifacts/swift/smoke SWIFT_INIT_FROM=artifacts/dart/context512-literals-20261110-01/candidates/epoch-0006.pt
    caffeinate -i make train-swift SWIFT_DEVICE=mps SWIFT_EPOCHS=3 SWIFT_RUN=artifacts/swift/context512 SWIFT_INIT_FROM=artifacts/dart/context512-literals-20261110-01/candidates/epoch-0006.pt
    make evaluate-swift SWIFT_DEVICE=mps SWIFT_CHECKPOINT=artifacts/swift/context512/best.pt
    make challenge-swift SWIFT_DEVICE=mps SWIFT_CHECKPOINT=artifacts/swift/context512/best.pt
    caffeinate -i make continue-swift SWIFT_DEVICE=mps SWIFT_EPOCHS=3 SWIFT_CHECKPOINT=artifacts/swift/context512/last.pt

Use only compatible full checkpoints from artifacts for transfer. Resume full
last.pt in its original run; archive selected full candidates before continuation.
Inference-only packs/*/model/model.pt and ONNX are never resumable checkpoints.
Review natural validation code, independent Golden and displayed source before
freezing one candidate and first adaptive test. Stop at a useful bounded baseline;
retain measured limits rather than optimizing a single aggregate score.

Data stays under ~/Datasets/neural-semantic-highlighting/swift. Immutable family
splits, source/license provenance and copy exclusion follow other standalone packs.
Full optimizer/RNG checkpoints, invocation settings and epoch timings stay under
artifacts/swift. Browser inference requires no Swift SDK, parser or Python process.
