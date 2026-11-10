# Dart training

Use the existing shared four-layer, width-128, 512-byte model and Python/PyTorch
environment. No Dart or Flutter SDK is installed or required.

    make dataset-dart
    make test-labeling-dart
    caffeinate -i make train-dart-smoke DART_DEVICE=mps DART_RUN=artifacts/dart/smoke DART_INIT_FROM=artifacts/csharp/context512-mixed-20261109-01/candidates/epoch-0003.pt
    caffeinate -i make train-dart DART_DEVICE=mps DART_EPOCHS=3 DART_RUN=artifacts/dart/context512 DART_INIT_FROM=artifacts/csharp/context512-mixed-20261109-01/candidates/epoch-0003.pt
    make evaluate-dart DART_DEVICE=mps DART_CHECKPOINT=artifacts/dart/context512/best.pt
    make challenge-dart DART_DEVICE=mps DART_CHECKPOINT=artifacts/dart/context512/best.pt
    caffeinate -i make continue-dart DART_DEVICE=mps DART_EPOCHS=3 DART_CHECKPOINT=artifacts/dart/context512/last.pt

Initialize only compatible full checkpoints; continue the full last.pt, never
inference .pt or ONNX. Archive selected full candidates before continuation.
Review independent Golden, actual natural validation and displayed code, then
freeze before first adaptive test. Stop at a useful bounded baseline and retain
known limits. Keep unseen, focus and visible evidence distinct. Data stays under
~/Datasets/neural-semantic-highlighting/dart; full optimizer/RNG checkpoints,
invocations and measured times under artifacts/dart.
