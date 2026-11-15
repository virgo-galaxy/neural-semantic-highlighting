# TOML training

Use the shared 894,872-parameter, 512-byte Transformer on the existing MPS host.
No new SDK or global package is installed. Pinned toml parser assets are verified in project cache and use existing Node.

    make dataset-toml
    make test-labeling-toml
    caffeinate -i make train-toml-smoke TOML_DEVICE=mps TOML_RUN=artifacts/toml/smoke TOML_INIT_FROM=artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt
    caffeinate -i make train-toml TOML_DEVICE=mps TOML_EPOCHS=3 TOML_RUN=artifacts/toml/context512 TOML_INIT_FROM=artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt
    caffeinate -i make continue-toml TOML_DEVICE=mps TOML_EPOCHS=3 TOML_CHECKPOINT=artifacts/toml/context512/last.pt

Initialize only from compatible full checkpoints under artifacts. Resume complete
last.pt in its original run; archive best full candidates before continuation.
Inference packs/*/model/model.pt and ONNX are never resumable checkpoints.
Review actual natural validation, independent Golden and displayed source before
freezing a candidate and first adaptive test. Keep language/script and natural /
focus / visible evidence distinct. Stop at a useful bounded baseline and preserve
measured limits, every prior snapshot, experiment and formal model.

External data stays under ~/Datasets/neural-semantic-highlighting/toml. Full
optimizer/RNG checkpoints, invocation settings and measured epoch timings stay
under artifacts/toml. Frontend consumers require no TOML or Python process.
