# Swift baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Macro F1
averages represented roles; declaration modifiers are separate. This measures
official parser/source-local Gold, not compiler type correctness, framework APIs,
project analysis, macro expansion or every Swift release.

| Evidence           | Documents | Exact-span F1 | Role macro F1 |
| ------------------ | --------: | ------------: | ------------: |
| Natural validation |        23 |        93.60% |        78.19% |
| Focus validation   |       183 |        91.95% |        72.21% |
| First natural test |        22 |        93.65% |        85.01% |
| First focus test   |       159 |        94.85% |        88.92% |

Frozen full candidate: `artifacts/swift/context512-mixed-20261111-01/candidates/epoch-0006.pt`. Fixed natural validation macro
F1 0.7581 selects within the mixed-source run.
Ten actual natural validation sources, 28 independent Golden and eight display
files were reviewed before the freeze and first adaptive test. No training
followed the test. Combined natural/focus scores are not real-source accuracy.

## Corpus and grouping

Prepared snapshot: `dad07da8cd39f28113a0cd7718ca3234b5c51888cec2e6024cccc4901df3ddac`. 2,158 input records,
96 exact duplicates merged,
44 cross-family lexical/normalized copy documents excluded,
2,018 retained. Frozen assignments preserve all 230 initial
retained families and extend to 242 before mixed-source training.

238 immutable Git-pinned files come from Collections, Algorithms, Async Algorithms,
HTTP Types, Alamofire and Apple's Food Truck SwiftUI sample, with complete root
licenses/notices, blob hashes and original bytes. The original task curriculum
contains 68 families (1,632 variants); review adds 12 separate mixed literal/closure
families (288 variants). All 2,158 final inputs pass parsing and complete original
coverage: zero final quarantines in this bounded capture. Earlier Gold snapshots,
including the three literal-trivia quarantines that prompted correction, remain.
Golden and displayed source never enter collection roots.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          189 |       1442 |    3326 |
| validation |           23 |        183 |     415 |
| test       |           22 |        159 |     382 |

Copy auditing and intact source families precede windowing; revisions retain
assignments. Natural/focus windows remain separate. The 22 natural test files and
six captured projects limit generalization claims; this is not a whole ecosystem
or compiler certification. Source, licenses, all corpus/Gold/prepared revisions and
full experiments remain under ~/Datasets/neural-semantic-highlighting/swift and
artifacts/swift, outside the committed inference bundle.

## Environment, Gold and bounded training

The existing toolchain was explicitly upgraded to Swift 6.4.2 in the preceding
environment task. This language task installs no SDK, package or global dependency.
Our parse-only helper links the installed official SwiftParser/SwiftSyntax libraries;
compiler, library, helper-source and helper-binary hashes are retained. It never
executes collected projects, follows imports or expands macros. Parser errors,
missing/unmapped tokens and original-byte/Unicode coverage gaps fail closed.
Multi-line literal continuation trivia and function-type/enum/accessor parameter
roles were corrected before the first trained snapshot; earlier evidence remains.

The model has **894,872 parameters**, four layers, width 128, four heads, FFN 512
and **512 original UTF-8 bytes** of context. Smoke precedes three initial epochs
transferred from the compatible full Dart epoch-6 checkpoint. Initial full Swift
epoch 2 initializes a fresh mixed-source run at learning rate 0.00015; three epochs
and three optimizer/RNG-resumed epochs select mixed epoch 6. All nine non-smoke
epochs take 196.8 seconds in total,
roughly 20–23 seconds each. Exact invocations/times and initial configuration
serialization remain in reports/experiments.json and the archived runs. Inference
.pt/ONNX files never initialize or resume training.

## Actual code and independent visible probes

The eight displayed files aggregate **92.16%**.
The two SwiftUI examples score about 97.7%; mixed strings remain weaker. Ten
natural validation files were inspected directly across Apple SwiftUI, Alamofire,
Collections and Async Algorithms; their final F1 range is
90.75%–96.19%.
These are visible development diagnostics, not unseen test scores.

| Display           | Exact-span F1 |
| ----------------- | ------------: |
| bindings.swift    |        97.73% |
| collections.swift |        92.37% |
| concurrency.swift |        96.09% |
| generics.swift    |        92.17% |
| hello.swift       |        87.74% |
| patterns.swift    |        92.52% |
| strings.swift     |        79.79% |
| swiftui.swift     |        97.67% |

The separate teacher passes all 28 manually marked cases and 12 tests. Neural
output exactly matches spans, roles and modifiers in **13/28** cases;
full missing/unexpected diagnostics remain. All eight examples pass official
Swift 6.4.2 parsing/coverage. Six also typecheck with that compiler. The current
macOS 27 CLI SDK exposes a SwiftUI State macro whose plugin is absent, so the two
common SwiftUI examples additionally typecheck with preserved Xcode Swift 6.0.3 /
macOS 15.2 SDK. No SDK/plugin is installed and no latest-framework compatibility
claim is made. This compiler limitation does not affect neural browser inference.

Known errors include raw/multi-line/interpolated/regex boundaries, dollar-name
splits, constructors/imported calls, generics/enums, local roles and declaration
flags. No runtime parser, source scanner or spelling-based repair masks them.
Browser/native parity and original text checks establish consistency, not perfect
semantic accuracy. This is a bounded usable baseline; further tuning stops here.
