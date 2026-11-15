# INI training

Use the shared 894,872-parameter, 512-byte Transformer on the existing MPS host.
No new SDK or global package is installed. The existing Python standard-library ConfigParser supplies independent structure validation.

    make dataset-ini
    make test-labeling-ini
    caffeinate -i make train-ini-smoke INI_DEVICE=mps INI_RUN=artifacts/ini/smoke INI_INIT_FROM=artifacts/toml/context512-refine-20261115-01/candidates/epoch-0002.pt
    caffeinate -i make train-ini INI_DEVICE=mps INI_EPOCHS=3 INI_RUN=artifacts/ini/context512 INI_INIT_FROM=artifacts/toml/context512-refine-20261115-01/candidates/epoch-0002.pt
    caffeinate -i make continue-ini INI_DEVICE=mps INI_EPOCHS=3 INI_CHECKPOINT=artifacts/ini/context512/last.pt

Initialize only from compatible full checkpoints under artifacts. Resume complete
last.pt in its original run; archive best full candidates before continuation.
Inference packs/*/model/model.pt and ONNX are never resumable checkpoints.
Review actual natural validation, independent Golden and displayed source before
freezing a candidate and first adaptive test. Keep language/script and natural /
focus / visible evidence distinct. Stop at a useful bounded baseline and preserve
measured limits, every prior snapshot, experiment and formal model.

External data stays under ~/Datasets/neural-semantic-highlighting/ini. Full
optimizer/RNG checkpoints, invocation settings and measured epoch timings stay
under artifacts/ini. Frontend consumers require no INI parser, language SDK or Python process.
