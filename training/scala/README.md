# Scala training

Reuse the shared 894,872-parameter, 512-byte model and existing MPS environment.
Offline supervision compiles only pinned CST sources with existing Clang. No Scala
SDK, sbt, compiler environment, package or global dependency is installed.

    make dataset-scala
    make test-labeling-scala
    caffeinate -i make train-scala-smoke SCALA_DEVICE=mps SCALA_RUN=artifacts/scala/smoke SCALA_INIT_FROM=artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt
    caffeinate -i make train-scala SCALA_DEVICE=mps SCALA_EPOCHS=3 SCALA_RUN=artifacts/scala/context512 SCALA_INIT_FROM=artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt
    caffeinate -i make continue-scala SCALA_DEVICE=mps SCALA_EPOCHS=3 SCALA_CHECKPOINT=artifacts/scala/context512/last.pt

Initialize only from compatible full checkpoints under artifacts. Resume complete
last.pt in its original run; archive best full candidates before continuation.
Inference packs/*/model/model.pt and ONNX are never resumable checkpoints.
Review actual natural validation, independent Golden and displayed source before
freezing a candidate and first adaptive test. Keep language/script and natural /
focus / visible evidence distinct. Stop at a useful bounded baseline and preserve
measured limits, every prior snapshot, experiment and formal model.

External data stays under ~/Datasets/neural-semantic-highlighting/scala. Full
optimizer/RNG checkpoints, invocation settings and measured epoch timings stay
under artifacts/scala. Frontend consumers require no JVM, Scala or Python process.
