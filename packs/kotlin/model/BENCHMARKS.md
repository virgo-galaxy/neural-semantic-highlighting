# Kotlin baseline evaluation

Exact-span F1 requires matching original UTF-16 start/end and role. Role macro F1
averages represented roles; declaration modifiers are separate. This evaluates
official PSI/source-local Gold, not compiler type correctness, resolved JVM or
Android APIs, Gradle execution, complete project analysis or all Kotlin releases.

| Evidence   | Profile       | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | ------------- | ------- | --------: | ------------: | ------------: |
| Validation | kotlin        | natural |        21 |        92.74% |        81.47% |
| Validation | kotlin        | focus   |       207 |        95.10% |        76.97% |
| Validation | kotlin-script | natural |         4 |        95.06% |        74.53% |
| Validation | kotlin-script | focus   |        24 |        93.42% |        95.64% |
| First test | kotlin        | natural |        26 |        94.70% |        76.42% |
| First test | kotlin        | focus   |       207 |        95.34% |        87.35% |
| First test | kotlin-script | natural |         5 |        93.51% |        71.05% |
| First test | kotlin-script | focus   |        24 |        93.75% |        92.84% |

Code/script natural test aggregate: **94.57%**
across 31 files, macro
76.86%. Focus or combined-corpus scores
must not be presented as real-source accuracy. Natural validation currently
contains stdlib code and serialization scripts; the first natural test includes
Compose sample code, coroutines and stdlib, with coroutines scripts. These small
family holdouts limit ecosystem and framework compatibility claims.

## Frozen selection and data

Full candidate: `artifacts/kotlin/context512-mixed-20261111-01/candidates/epoch-0003.pt`, epoch 3.
SHA-256: `ef8d69257c57b0ac29f04eda3aa762cc1a017fc826282608cd74fdb9e9344cc5`. Fixed mean per-profile natural validation
role macro F1 (0.8044) selects within the mixed-source
run. Review, freeze and the first adaptive test follow in that order. No training
follows that test. Golden and displayed files never enter collection roots.

Prepared snapshot: `128be8bef320fa9fa3d4b4f64dadaebe823c751170aa4862313f7757352cc5f5`. 2,555 inputs,
102 exact duplicates merged,
4 cross-family copy documents excluded,
2,449 retained. All 157 initial family assignments remain
unchanged; 12 independent mixed families extend the frozen set to 169.

Four official upstream projects provide 279 pinned original files: Kotlin stdlib,
Kotlinx Coroutines, Kotlinx Serialization and Android Compose samples. Complete
original licenses/notices and Git blob hashes are retained. The shared collector
excludes four captured files in reserved `model` paths, leaving 275 natural inputs;
all 279 originals remain preserved. Original task sources provide 69 code and 14
script families (1,992 variants), plus 12 separate mixed families (288 variants).
All 2,555 collected inputs pass official parsing and full original coverage, with
zero quarantines. Initial and final corpus/Gold/prepared snapshots remain immutable.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          214 |       1717 |    3676 |
| validation |           25 |        231 |     455 |
| test       |           31 |        231 |     454 |

Source families and copy audits precede windowing. Natural/focus windows remain
separate. Source, locks, licenses, raw corpus, Gold, prepared snapshots and full
training runs remain in ~/Datasets/neural-semantic-highlighting/kotlin and
artifacts/kotlin, outside committed inference bundles.

## Environment, teacher and short experiments

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**894,872 parameters**: four layers, width 128, four heads, FFN 512 and **512 original
UTF-8 bytes** of context. Smoke and six initial epochs transfer from the compatible
full Swift epoch-6 checkpoint. Initial Kotlin epoch 4 starts the separate mixed
run at learning rate 0.00015; all measured invocations, optimizer/RNG resumptions
and timings are in reports/experiments.json. The 12
non-smoke epochs take 321.5 seconds in total. Inference weights never
initialize or resume training.

No Kotlin SDK, Gradle, Android SDK or global dependency is installed. Official
2.4.21 embeddable compiler/parser JARs, with Maven checksums and strong hashes,
remain only in ignored project cache. The existing JDK compiles the parse-only
helper. Its LF view maps exactly back to original CRLF/CR/BOM UTF-16 positions;
source/training bytes are unchanged. Parse errors, unknown tokens and Unicode or
coverage gaps fail closed. Input code/scripts, imports, dependencies, annotations
and compiler plugins never execute. The teacher passes 32 manually marked Golden
cases and 13 focused tests, independently of neural predictions.

## Visible and real-code review

Eight displayed sources aggregate **92.74%**.
Ten actual natural validation files across code and script are inspected before
freeze, with F1 from 81.35% to
98.42%. Full diagnostics are retained;
long upstream token excerpts are bounded. These are development probes, not
additional held-out test results.

| Display          | Exact-span F1 |
| ---------------- | ------------: |
| build.gradle.kts |        98.18% |
| collections.kt   |        93.88% |
| compose.kt       |        94.57% |
| coroutines.kt    |        94.78% |
| generics.kt      |        95.45% |
| hello.kt         |        89.70% |
| models.kt        |        94.37% |
| strings.kt       |        76.51% |

Neural spans/roles/modifiers are entirely exact in **16/32**
Golden cases. All eight authored examples parse with complete original coverage.
Six ordinary JVM examples also compile with the official cached compiler and
stdlib/coroutines dependencies on the existing JDK, without execution. The Compose
and Gradle examples are parse-only: no Android framework or Gradle installation,
execution, dependency resolution or plugin validation is claimed.

Raw and multi-dollar string boundaries, implicit receivers/it, imported calls,
generics and distant symbols remain approximate. No runtime parser, regular
expression, capitalization rule or source-spelling repair masks neural errors.
Browser/native parity establishes consistent execution rather than perfect semantics.
This selected baseline is bounded and usable; further tuning stops here.
