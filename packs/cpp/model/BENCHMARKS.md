# C++ baseline evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match.
Role macro F1 averages represented roles; declaration modifiers are scored
separately. This is bounded source-local syntax supervision, not Clang project
semantics, template instantiation or overload resolution. Natural source, focus
tasks and visible development probes are distinct evidence.

| Evidence           | Documents | Exact-span F1 | Role macro F1 |
| ------------------ | --------: | ------------: | ------------: |
| Natural validation |        16 |        95.13% |        79.47% |
| Focus validation   |       144 |        89.78% |        71.43% |
| First natural test |        14 |        92.67% |        72.89% |
| First focus test   |       120 |        96.48% |        82.07% |

Frozen full checkpoint: `artifacts/cpp/context512-mixed-v2-20261109-01/candidates/epoch-0002.pt`, epoch 2.
Selection maximized natural fixed-validation role macro F1
(0.8248). Natural validation source and visible
probes were reviewed before the first adaptive test. No training followed that
test; its source and results are known evidence for future comparisons.

## Data and protocol

Immutable snapshot: `8f8af2fad3cd72da85820d6256192db5b72cf47da17f8f36c32dfe34285109a1`.
1,686 input records; 0 exact duplicate records merged;
0 cross-family copy records excluded; 1,686 retained.
190 source/task family assignments are frozen before windows. Exact,
lexical and normalized copies are audited before grouped allocation. Related
headers/implementations and every task variant stay together. Golden and
Playground are excluded from collection roots.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          120 |       1272 |    2082 |
| validation |           16 |        144 |     244 |
| test       |           14 |        120 |     220 |

The bounded capture pins 7 fmt 11.1.4, 90 Catch2 3.8.1, 60 spdlog 1.15.2 and
50 LevelDB 1.23 files. `upstreams.json` retains exact commits and per-file blobs;
complete licenses, original bytes and locks remain external. Fifty-seven captured
files outside the pinned grammar were quarantined with exact source/error identities,
including all seven fmt captures. Accepted natural data therefore comes from the
other three projects. No fallback parser relabels unsupported files.
The original focus curriculum has 1,248 tasks across 52 complete families.
The final mixed-v2 capture adds 288 tasks across 12 independent families. All 178
original family allocations are retained and extended to 190. An intermediate
mixed-v1 snapshot excluded 48 cross-family copies; it and its short experiment
remain archived. A revised task structure removed the overlap before the final
zero-copy-exclusion snapshot was frozen. No old dataset or run was overwritten.

Gold uses official pinned Tree-sitter 0.25.10 / C++ grammar 0.23.4 source blobs.
The existing Apple Clang 21 and matching SDK compile only that offline parser;
authored C++17/20/23 option probes compiled and ran, and the displayed `.cpp`
files passed C++20 syntax checks. No compiler/SDK/global package was installed.
Collected projects never compile or execute; includes/macros are not followed or
expanded. Parser/source/compiler/binary identities accompany immutable Gold.

## Visible source review

Ten natural validation files across source lengths and upstreams, eight authored
display examples and independent manually marked Golden cases guide development.
These are not another held-out test score.

| Display probe      | Exact-span F1 |
| ------------------ | ------------: |
| algorithms.cpp     |        97.00% |
| bindings.cpp       |        93.98% |
| classes.cpp        |        92.86% |
| concepts.cpp       |        97.06% |
| hello.cpp          |        92.19% |
| raw-strings.cpp    |        83.02% |
| smart-pointers.cpp |        93.15% |
| templates.hpp      |        98.73% |

Neural Golden matched all spans and modifiers exactly in 11/29
cases. The teacher separately passes all 29 marked cases. Full source,
missing/unexpected spans and role/modifier diagnostics remain in `reports/`.

## Training and inference

Unchanged architecture: 894,743 parameters, four layers, width 128,
four heads, FFN 512 and 512 original UTF-8 bytes per window. Initial weights come
explicitly from the full selected C training checkpoint in `artifacts/c`, with
fresh optimizer/RNG state and new C++ labels. The first experiment ran three
initial plus six bounded continuation epochs, selecting epoch 8. An intermediate
mixed-v1 trial ran three epochs. The final mixed-v2 experiment starts afresh from
the complete first-run epoch-8 checkpoint and runs three epochs at learning rate
0.0001. Its own natural fixed-validation metric selects the final candidate.
Measured epochs take about 9–12 seconds on MPS. Checkpoints, timing, dataset identity
and invocation logs remain under `artifacts/cpp`; prior language models stay intact.

Adaptive inference consumes original text and predicted boundaries, never Gold
cuts, a compiler, SDK, parser or source-regex correction. Long code uses multiple
windows, with bounded context for long literals/templates and distant declarations.
Selected native float32 weights and ONNX exports are verified separately from
language quality; runtime parity cannot remove model/teacher limits.
