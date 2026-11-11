# Kotlin training

Reuse the shared four-layer, width-128, 512-byte Transformer and existing Python /
PyTorch MPS environment. The existing JDK runs fixed official Kotlin parser JARs
from project cache. No Kotlin SDK, Gradle, Android SDK or global dependency is
installed for supervision. Collected source/scripts are never built or executed.

    make dataset-kotlin
    make test-labeling-kotlin
    caffeinate -i make train-kotlin-smoke KOTLIN_DEVICE=mps KOTLIN_RUN=artifacts/kotlin/smoke KOTLIN_INIT_FROM=artifacts/swift/context512-mixed-20261111-01/candidates/epoch-0006.pt
    caffeinate -i make train-kotlin KOTLIN_DEVICE=mps KOTLIN_EPOCHS=3 KOTLIN_RUN=artifacts/kotlin/context512 KOTLIN_INIT_FROM=artifacts/swift/context512-mixed-20261111-01/candidates/epoch-0006.pt
    make evaluate-kotlin KOTLIN_DEVICE=mps KOTLIN_CHECKPOINT=artifacts/kotlin/context512/best.pt
    make challenge-kotlin KOTLIN_DEVICE=mps KOTLIN_CHECKPOINT=artifacts/kotlin/context512/best.pt
    caffeinate -i make continue-kotlin KOTLIN_DEVICE=mps KOTLIN_EPOCHS=3 KOTLIN_CHECKPOINT=artifacts/kotlin/context512/last.pt

Initialize only from compatible full checkpoints under artifacts. Resume complete
last.pt in its original run; archive best full candidates before continuation.
Inference packs/*/model/model.pt and ONNX are never resumable checkpoints.
Review actual natural validation, independent Golden and displayed source before
freezing a candidate and first adaptive test. Keep language/script and natural /
focus / visible evidence distinct. Stop at a useful bounded baseline and preserve
measured limits, every prior snapshot, experiment and formal model.

External data stays under ~/Datasets/neural-semantic-highlighting/kotlin. Full
optimizer/RNG checkpoints, invocation settings and measured epoch timings stay
under artifacts/kotlin. Frontend consumers require no JVM, Kotlin or Python process.
