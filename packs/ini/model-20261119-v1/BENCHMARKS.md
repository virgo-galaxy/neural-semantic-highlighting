# INI baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Role macro F1
averages represented roles; declaration modifiers are separate. It measures
independent ConfigParser-checked original INI ranges and source-local roles, not application
schema validity, configuration execution, template execution or syntax validation
by the runtime highlighter.

| Evidence   | Profile | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | ------- | ------- | --------: | ------------: | ------------: |
| Validation | ini     | natural |         7 |        94.31% |        91.38% |
| Validation | ini     | focus   |       167 |        89.86% |        89.15% |
| First test | ini     | natural |         8 |        89.70% |        90.88% |
| First test | ini     | focus   |       120 |        91.28% |        89.58% |

Natural test aggregate: **89.70%** across
8 real files. Focus and combined-corpus scores
must not be presented as real-code accuracy. Small family holdouts from bounded
captures do not certify an entire language ecosystem or dependency environment.

## Data and frozen selection

103 Git-pinned original files come from Fail2ban, Geany, Meson, CPython, setuptools.
Original root licenses/notices, Git blob hashes and source bytes remain preserved.
The final curriculum has 52 families / 1248 variants.
Original Git commit/tree/blob identities and licenses are preserved. Fixed ConfigParser/range validation precedes bounded selection; candidate rejection inventory is retained. Known upstream INI paths keep their original filenames without making general .conf or cross-file extension claims. A separate 12-family/288-task mixed extension follows observed continuation/version/opaque-value errors, preserving all 102 original family assignments and the initial six-epoch run.
Golden, tests and displayed source never enter collection roots. Corpus/Gold /
prepared revisions remain immutable; exact and cross-family copies are audited
before windowing, and 114 source-family assignments are frozen before training.

Prepared snapshot: `72cb31aee90dadd65b397ae95cfafa6e8935e86f5242717b0da165d6c62ef13b`. 1351 Gold inputs,
3 exact duplicates merged,
14 cross-family copy documents excluded,
1334 retained. Final Gold accepts 1351 files and
quarantines 0; rejected originals remain retained, never rewritten.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |           74 |        958 |    1393 |
| validation |            7 |        167 |     203 |
| test       |            8 |        120 |     156 |

Full candidate: `artifacts/ini/context512-refine-20261115-01/candidates/epoch-0002.pt`, epoch 2.
SHA-256: `ad760bada3d9329f10eb5c186d7a3460f16395b2c4ec8e2fa598803b79010172`. Fixed mean per-profile natural validation
role macro F1 (0.8424) selects within its run.
Run selection is phase-local. The final lower-learning-rate candidate was kept
after visible continuation/server review; it does not maximize the fixed-window
score across all historical phases.
Review precedes freeze and the first adaptive test; no training follows that test.
Source, locks, licenses, every snapshot and full optimizer/RNG experiment remain
under ~/Datasets/neural-semantic-highlighting/ini and artifacts/ini, outside the
committed inference bundle.

## Environment and short training

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**894,872 parameters**: four layers, width 128, four heads, FFN 512, and **512 original
UTF-8 bytes** of context. Smoke precedes short three-epoch phases, initialized from
the compatible full `artifacts/toml/context512-refine-20261115-01/candidates/epoch-0002.pt`. The initial curriculum batch size is 32; mixed training raises it to 64 after
observed continuation/value-boundary errors, with full natural-source coverage.
A final three-epoch refinement uses learning rate 0.0001.
All 15 non-smoke epochs take
93.1 seconds; exact invocations, resumptions and timings remain in
reports/experiments.json. Inference .pt/ONNX never initialize or resume training.

No language SDK/interpreter or global dependency is installed. Offline tooling:
Existing CPython 3.12 ConfigParser with interpolation disabled, independent section/key inventory validation and Python/stdlib/teacher SHA-256 provenance; no downloaded tool or SDK. Fixed revisions, original licenses/blob hashes, compiler and binary
provenance are retained. Collected source/dependencies never execute. Parser
acceptance is not application/dialect validity. Parser errors, original coverage and Unicode
boundary failures quarantine input. Original CRLF and Unicode text remain unchanged.

## Real and independently visible review

Eight authored displays aggregate **95.17%**.
7 actual natural validation sources were inspected before freeze; F1 ranges
89.66%–100.00%.
These are visible development diagnostics, not additional unseen test evidence.
Long upstream diagnostic excerpts are bounded in committed reports.

| Display           | Exact-span F1 |
| ----------------- | ------------: |
| .editorconfig     |        97.67% |
| continuations.ini |        82.76% |
| hello.ini         |       100.00% |
| logging.ini       |       100.00% |
| paths.ini         |        94.44% |
| server.ini        |        97.22% |
| setup.cfg         |        89.47% |
| tox.ini           |        97.14% |

The teacher passes 40 separately hand-marked Golden cases and
12 focused tests. Neural spans, roles and modifiers are entirely
exact in **17/40** Golden cases. All eight
examples pass the recorded offline teacher and complete original coverage; no SDK/compiler
execution, dependency compatibility or package API validity is claimed.

Indented continuation lines resembling assignments or headers can split or gain property/punctuation roles (continuations.ini display 82.76% F1). Packaging constraints/version strings and empty-value continuations remain weaker (setup.cfg 89.47%); quoted/path values and section/glob boundaries can also fragment. Common INI/EditorConfig source uses one explicit dialect: #/; full-line comments, with inline value markers kept literal. Application-specific inline comments/escape rules and general .conf/.env syntax are outside scope. No interpolation, configuration execution, project validation or runtime parser/spelling repair is provided. No runtime parser, regular expression or source-spelling
repair masks prediction errors. Browser/native parity and original-text checks
establish consistent execution rather than perfect semantics. This is a bounded
usable baseline; tuning stops after its freeze and first test.
