# R training

Use the shared 894,872-parameter, 512-byte Transformer on the existing MPS host.
No R SDK/interpreter is installed. Offline CST sources compile only in project cache.

    make dataset-r
    make test-labeling-r
    caffeinate -i make train-r-smoke R_DEVICE=mps R_RUN=artifacts/r/smoke R_INIT_FROM=artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt
    caffeinate -i make train-r R_DEVICE=mps R_EPOCHS=3 R_RUN=artifacts/r/context512 R_INIT_FROM=artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt
    caffeinate -i make continue-r R_DEVICE=mps R_EPOCHS=3 R_CHECKPOINT=artifacts/r/context512/last.pt

Initialize only from compatible full checkpoints under artifacts. Resume complete
last.pt in its original run; archive best full candidates before continuation.
Inference packs/*/model/model.pt and ONNX are never resumable checkpoints.
Review actual natural validation, independent Golden and displayed source before
freezing a candidate and first adaptive test. Keep language/script and natural /
focus / visible evidence distinct. Stop at a useful bounded baseline and preserve
measured limits, every prior snapshot, experiment and formal model.

External data stays under ~/Datasets/neural-semantic-highlighting/r. Full
optimizer/RNG checkpoints, invocation settings and measured epoch timings stay
under artifacts/r. Frontend consumers require no JVM, R or Python process.
