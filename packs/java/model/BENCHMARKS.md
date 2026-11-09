# Java baseline evaluation

Exact-span F1 requires original UTF-16 token start, end and semantic role to match.
Role macro F1 averages represented roles; declaration-modifier results are separate
in the raw JSON. Natural code, focused tasks and visible probes are distinct evidence.

| Evidence                          | Documents | Exact-span F1 | Role macro F1 |
| --------------------------------- | --------: | ------------: | ------------: |
| Adaptive natural validation (MPS) |        29 |        95.11% |        86.61% |
| Adaptive focus validation (MPS)   |       160 |        92.38% |        73.23% |
| First natural test (MPS)          |        29 |        92.60% |        82.28% |
| First focus test (MPS)            |       160 |        94.95% |        86.32% |

Selected complete checkpoint: `artifacts/java/context512-mixed-20261109-01/candidates/epoch-0001.pt`. This is epoch 1 of the mixed-syntax
revision, selected by natural fixed-validation role macro F1
(0.8674), not by the held-out test. The run
completed three short epochs; later epochs did not improve that selection metric.
A separate nine-epoch initial experiment is preserved. The selected revision starts
with explicit weights-only transfer from its complete epoch-9 checkpoint, resetting
optimizer/RNG for a new dataset identity. The effective selected lineage is ten
training epochs, while twelve epochs were run for development/selection in total.

Natural validation, ten short real validation files, independent Golden and seven
separately authored displayed examples were reviewed before first test inspection.
No tuning followed the first test. Those archived test files are known for future
comparisons, not a fresh independent test on subsequent revisions.

## Data and lineage

Final immutable snapshot: `7b8d5f36c75052d120aeaa28477dea9fa7b4a47f28012cbb0e8f93c0bf55f878`.
1,752 input records, 2 exact duplicate records merged,
25 cross-family copies excluded; 1,725 retained records.
Exact, lexical and identifier-normalized copy checks run before grouped windows.
All 323 original family assignments were preserved and extended to 341 before the
mixed revision trained. Golden and Playground are excluded from all collection roots.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          229 |       1118 |    3701 |
| validation |           29 |        160 |     452 |
| test       |           29 |        160 |     452 |

The source capture contains 90 Apache Commons Lang files at
`5b59487808d0b86a94ad7a1ebd4c200e09b7be09`, 65 Gson files at
`686fad782d969d8f15c7581a5435a208b810caa7`, two completed Spring Guide sources at
`e15fec6773dc1eb6028055630e3e68cbd8653240`, and 155 bounded local OpenJDK 22.0.1
source files. Original source bytes, complete licenses, archive/member hashes and
Git blob/revision locks remain external under the Java dataset directory.
Focused data contains 864 original syntax tasks and 576 mixed-program/module tasks;
related variants retain a source family. Some exact duplicates are merged.

The pinned OpenJDK 22 scanner and parse-only AST provide bounded local Gold roles;
this is not full project symbol resolution or Java execution compatibility. Neither
Maven/Gradle nor source dependencies, annotation processors or collected source code
are installed/built/executed. Modern syntax coverage uses focused tasks as well as
natural code, rather than claiming the small library holdout certifies every release.

## Real display checks

| Separately authored display probe | Exact-span F1 |
| --------------------------------- | ------------: |
| Annotations.java                  |        94.67% |
| AsyncTasks.java                   |       100.00% |
| Hello.java                        |        96.19% |
| PatternRouting.java               |        94.05% |
| Result.java                       |        96.43% |
| TextTemplates.java                |       100.00% |
| module-info.java                  |        89.47% |

All seven display probes are development evidence. 3 of 17 independent
visible Golden probes are exact including declaration modifiers; the remaining
small probes have explicit differences in `reports/golden.json`. This count is not
a pooled corpus accuracy and includes fine local role/flag distinctions that may
share display colors. Read KNOWN_ISSUES.md with both corpus and real-code reports.

## Architecture and training budget

Four Transformer layers, width 128, four heads, FF512, 512-byte context,
894,614 parameters. The first Java experiment initialized from the full Go checkpoint
`artifacts/go/context512-20260913-074648-569634/best.pt`; no inference-only export was
used as a training checkpoint. A smoke reload/inference test preceded 3 initial +
6 continuation epochs. A bounded mixed-data revision ran 3 epochs at learning rate
0.0001. Epochs took roughly 28–39 seconds on this host's MPS device; `caffeinate -i`
prevented idle sleep. No long training campaign or model enlargement was required.

All runs, optimizer/RNG state, dataset revisions and frozen candidates remain in
ignored artifacts. Selected float32 inference and ONNX exports preserve the reviewed
weights and are not resumable checkpoints. No existing language model was replaced.
