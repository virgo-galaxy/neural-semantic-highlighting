# Zig training

Targets **0.17.1 only** using the existing shared four-layer, width-128,
512-byte architecture. Offline data stays under
`~/Datasets/neural-semantic-highlighting/zig`; complete optimizer/RNG checkpoints,
logs and experiments under `artifacts/zig`.

```sh
make dataset-zig
make test-labeling-zig
caffeinate -i make train-zig-smoke ZIG_DEVICE=mps ZIG_RUN=artifacts/zig/smoke ZIG_INIT_FROM=artifacts/rust/context512-literals-20261110-01/candidates/epoch-0004.pt
caffeinate -i make train-zig ZIG_DEVICE=mps ZIG_EPOCHS=3 ZIG_RUN=artifacts/zig/context512 ZIG_INIT_FROM=artifacts/rust/context512-literals-20261110-01/candidates/epoch-0004.pt
make evaluate-zig ZIG_DEVICE=mps ZIG_CHECKPOINT=artifacts/zig/context512/best.pt
make challenge-zig ZIG_DEVICE=mps ZIG_CHECKPOINT=artifacts/zig/context512/best.pt
caffeinate -i make continue-zig ZIG_DEVICE=mps ZIG_EPOCHS=6 ZIG_CHECKPOINT=artifacts/zig/context512/last.pt
```

Use only compatible **complete training checkpoints** for transfer; resume the
run's `last.pt`. Never train from inference `.pt` or ONNX. Preserve archived full
candidates before continuation and all previous source/model/run history.
Review actual current source, Golden and authored display code before candidate
freeze and first adaptive test. Keep natural/focus/visible scores distinct, use
bounded measured runs and record remaining limitations instead of chasing one
score. Frontend consumers require none of this SDK/Gold environment.
