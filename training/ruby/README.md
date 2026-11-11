# Ruby training

Use the shared 894,872-parameter, 512-byte Transformer on the existing MPS host.
Pinned CST sources compile in project cache; no Ruby SDK, gem or global package
is installed. Source, heredocs, subshells, Rails/Rake projects and dependencies
are parsed only, never executed.

    make dataset-ruby
    make test-labeling-ruby
    caffeinate -i make train-ruby-smoke RUBY_DEVICE=mps RUBY_RUN=artifacts/ruby/smoke RUBY_INIT_FROM=artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt
    caffeinate -i make train-ruby RUBY_DEVICE=mps RUBY_EPOCHS=3 RUBY_RUN=artifacts/ruby/context512 RUBY_INIT_FROM=artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt
    caffeinate -i make continue-ruby RUBY_DEVICE=mps RUBY_EPOCHS=3 RUBY_CHECKPOINT=artifacts/ruby/context512/last.pt

Initialize only from compatible full checkpoints under artifacts. Resume complete
last.pt in its original run; archive best full candidates before continuation.
Inference packs/*/model/model.pt and ONNX are never resumable checkpoints.
Review actual natural validation, independent Golden and displayed source before
freezing a candidate and first adaptive test. Keep language/script and natural /
focus / visible evidence distinct. Stop at a useful bounded baseline and preserve
measured limits, every prior snapshot, experiment and formal model.

External data stays under ~/Datasets/neural-semantic-highlighting/ruby. Full
optimizer/RNG checkpoints, invocation settings and measured epoch timings stay
under artifacts/ruby. Frontend consumers require no Ruby or Python process.
