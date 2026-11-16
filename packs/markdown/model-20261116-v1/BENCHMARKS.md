# Markdown baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Role macro F1
averages represented roles; strong/emphasis/strikethrough modifiers are separate. It measures base Markdown spans against independent AST/source-local Gold,
not composed child semantic accuracy, Markdown document rendering, template
execution or every extension. Predicted fence routing is a separate visible diagnostic.

| Evidence   | Profile  | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | -------- | ------- | --------: | ------------: | ------------: |
| Validation | markdown | natural |        12 |        77.52% |        78.83% |
| Validation | markdown | focus   |       144 |        97.21% |        97.00% |
| First test | markdown | natural |        14 |        77.24% |        71.03% |
| First test | markdown | focus   |       120 |        98.21% |        97.08% |

Natural test aggregate: **77.24%** across
14 real files. Focus and combined-corpus scores
must not be presented as real-code accuracy. Small family holdouts from bounded
captures do not certify an entire language ecosystem or dependency environment.

## Data and frozen selection

116 Git-pinned original files come from Ant Design, TanStack Query, Vite, Redux Toolkit, TypeScript.
Original root licenses/notices, Git blob hashes and source bytes remain preserved.
The final curriculum has 64 families / 1536 variants.
Existing pinned public clones are reused without checkout changes, recollection or builds. Original Git tree/blob identities, bytes and licenses remain retained. One Liquid-extension document is quarantined. 40 structural families / 960 tasks are extended by 24 mixed wrapped-prose/link/frontmatter families / 576 tasks following actual validation/display review, preserving all 92 original assignments and experiments. Prose/link/code literal payloads normalize for structural-copy auditing; old-role behavior stays unchanged. Hand-marked Golden and display probes remain outside collection. The final source-family map has 116 retained families.
Golden, tests and displayed source never enter collection roots. Corpus/Gold /
prepared revisions remain immutable; exact and cross-family copies are audited
before windowing, and 116 source-family assignments are frozen before training.

Prepared snapshot: `13bcb693a1ee75a032f8dbd7655367381ac2447a3f3e56fd4ae2c52ff00f7af2`. 1651 Gold inputs,
0 exact duplicates merged,
2 cross-family copy documents excluded,
1649 retained. Final Gold accepts 1651 files and
quarantines 1; rejected originals remain retained, never rewritten.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |           87 |       1272 |    4006 |
| validation |           12 |        144 |     464 |
| test       |           14 |        120 |     408 |

Full candidate: `artifacts/markdown/context512-mixed-20261116-01/candidates/epoch-0005.pt`, epoch 5.
SHA-256: `a242673a7a0f39619fca26c2232806854e05d1f40bb98f5cc30d17b619624ce1`. Fixed mean per-profile natural validation
role macro F1 (0.7237) selects within its run.
The highest fixed natural validation macro score across the completed runs selects
mixed-run epoch 5. The later three-epoch refinement never improves that criterion,
so its weights remain archived and are not selected. Visible review checks the
chosen candidate before freeze; it does not use test results.
Review precedes freeze and the first adaptive test; no training follows that test.
Source, locks, licenses, every snapshot and full optimizer/RNG experiment remain
under ~/Datasets/neural-semantic-highlighting/markdown and artifacts/markdown, outside the
committed inference bundle.

## Environment and short training

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**894,227 parameters**: four layers, width 128, four heads, FFN 512, and **512 original
UTF-8 bytes** of context. Smoke precedes short three-epoch phases, initialized from
the compatible full `artifacts/xml/context512-refine-20261116-01/candidates/epoch-0003.pt`. Exact batch sizes, learning rates and phase budgets remain in the experiment
record; each phase preserves full natural-source coverage.
All 15 non-smoke epochs take
251.7 seconds; exact invocations, resumptions and timings remain in
reports/experiments.json. Inference .pt/ONNX never initialize or resume training.

No new language SDK/interpreter or global dependency is installed. Offline tooling:
Existing pinned Prettier 3.9.6 Markdown/remark/GFM parse-only assets, entities and Node, all file-hashed; no dependency or SDK installation. Fixed revisions, original licenses/blob hashes, compiler and binary
provenance are retained. Collected source/dependencies never execute. Parser
acceptance is not application/dialect validity. Parser errors, original coverage and Unicode
boundary failures quarantine input. Original CRLF and Unicode text remain unchanged.

## Real and independently visible review

Eight authored displays aggregate **87.05%**.
10 actual natural validation sources were inspected before freeze; F1 ranges
56.21%–86.89%.
These are visible development diagnostics, not additional unseen test evidence.
Long upstream diagnostic excerpts are bounded in committed reports.

| Display       | Exact-span F1 |
| ------------- | ------------: |
| code.md       |        87.80% |
| formatting.md |        78.16% |
| hello.md      |       100.00% |
| links.md      |        81.40% |
| lists.md      |       100.00% |
| mixed.md      |        92.68% |
| tables.md     |        87.50% |
| unicode.md    |        70.00% |

The teacher passes 48 separately hand-marked Golden cases and
14 focused tests. Neural spans, roles and modifiers are entirely
exact in **15/48** Golden cases. All eight
examples pass the recorded offline teacher and complete original coverage; no SDK/compiler
execution, dependency compatibility or package API validity is claimed.

This is an initial bounded Markdown baseline. On the natural holdout, embedded-code body exact-span F1 is 49.12% (19 reference bodies), heading F1 is 58.22% (180 spans), and prose text F1 is 60.52% (1304 spans); complete composed correctness is not established. Natural and visible evidence are base Markdown scores, not complete composed-code accuracy. Long wrapped prose, URL/title/reference boundaries, inline-code and raw-HTML/frontmatter boundaries remain approximate; strict Golden modifiers/boundaries are also weaker. Visible formatting.md is 78.16% F1, links.md 81.40%, and Unicode/frontmatter unicode.md 70.00%. The code.md Python body prediction omits its first import line, and an unknown-language body can be misclassified. Five of seven authored top-level code bodies have exact predicted body/info boundaries; TSX/JSON/CSS bodies in mixed.md and the XML body in unicode.md match. Composition runs on predicted regions only; it cannot fix missed/incorrect regions. Unknown/unregistered/recursive Markdown bodies remain code when their region is predicted. Nested/indented fences, front matter and raw HTML remain opaque; no MDX, math/template processing, Markdown document rendering, source execution or automatic language detection is claimed. Runtime performs no parser, regex or source-spelling repair. No runtime parser, regular expression or source-spelling
repair masks prediction errors. Browser/native parity and original-text checks
establish consistent execution rather than perfect semantics. This is a bounded
usable baseline; tuning stops after its freeze and first test.
