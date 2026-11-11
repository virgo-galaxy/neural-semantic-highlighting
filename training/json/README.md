# JSON / JSONC training

Use the shared 894,872-parameter, 512-byte Transformer on the existing MPS host.
No new SDK or global package is installed. Pinned jsonc-parser assets are verified in project cache and use existing Node.

    make dataset-json
    make test-labeling-json
    caffeinate -i make train-json-smoke JSON_DEVICE=mps JSON_RUN=artifacts/json/smoke JSON_INIT_FROM=artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt
    caffeinate -i make train-json JSON_DEVICE=mps JSON_EPOCHS=3 JSON_RUN=artifacts/json/context512 JSON_INIT_FROM=artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt
    caffeinate -i make continue-json JSON_DEVICE=mps JSON_EPOCHS=3 JSON_CHECKPOINT=artifacts/json/context512/last.pt

Initialize only from compatible full checkpoints under artifacts. Resume complete
last.pt in its original run; archive best full candidates before continuation.
Inference packs/*/model/model.pt and ONNX are never resumable checkpoints.
Review actual natural validation, independent Golden and displayed source before
freezing a candidate and first adaptive test. Keep language/script and natural /
focus / visible evidence distinct. Stop at a useful bounded baseline and preserve
measured limits, every prior snapshot, experiment and formal model.

External data stays under ~/Datasets/neural-semantic-highlighting/json. Full
optimizer/RNG checkpoints, invocation settings and measured epoch timings stay
under artifacts/json. Frontend consumers require no JSON / JSONC or Python process.
