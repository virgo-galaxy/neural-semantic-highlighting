# Rust training

Uses the existing shared four-layer, width-128, 512-byte architecture. Data stays
under `~/Datasets/neural-semantic-highlighting/rust`; full optimizer/RNG checkpoints
and logs under `artifacts/rust`. The Gold teacher is offline and source-local;
runtime inference imports no grammar, Rust SDK, Cargo or source heuristics.

```sh
make dataset-rust
make test-labeling-rust
caffeinate -i make train-rust-smoke RUST_DEVICE=mps RUST_RUN=artifacts/rust/smoke RUST_INIT_FROM=artifacts/cpp/context512-mixed-v2-20261109-01/candidates/epoch-0002.pt
caffeinate -i make train-rust RUST_DEVICE=mps RUST_EPOCHS=3 RUST_RUN=artifacts/rust/context512 RUST_INIT_FROM=artifacts/cpp/context512-mixed-v2-20261109-01/candidates/epoch-0002.pt
make evaluate-rust RUST_DEVICE=mps RUST_CHECKPOINT=artifacts/rust/context512/best.pt
make challenge-rust RUST_DEVICE=mps RUST_CHECKPOINT=artifacts/rust/context512/best.pt
caffeinate -i make continue-rust RUST_DEVICE=mps RUST_EPOCHS=6 RUST_CHECKPOINT=artifacts/rust/context512/last.pt
```

Initialize only from compatible complete training checkpoints; continue the
original run's `last.pt`. Never use `packs/*/model/model.pt` or ONNX as training
checkpoints. Archive reviewed full candidates before continuation. Review actual
natural validation, independent Golden and visible authored code before freezing
first adaptive test. Preserve all previous data/runs/models; stop at a useful,
bounded baseline and record controlled limitations rather than chase one score.
