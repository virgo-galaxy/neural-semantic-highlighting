# TOML baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Role macro F1
averages represented roles; declaration modifiers are separate. It measures
independent TOML AST/token ranges and source-local roles, not application
schema validity, configuration execution, template execution or syntax validation
by the runtime highlighter.

| Evidence   | Profile | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | ------- | ------- | --------: | ------------: | ------------: |
| Validation | toml    | natural |        10 |        99.03% |        96.35% |
| Validation | toml    | focus   |       117 |        97.22% |        96.93% |
| First test | toml    | natural |         9 |        99.10% |        97.52% |
| First test | toml    | focus   |        72 |        92.73% |        80.59% |

Natural test aggregate: **99.10%** across
9 real files. Focus and combined-corpus scores
must not be presented as real-code accuracy. Small family holdouts from bounded
captures do not certify an entire language ecosystem or dependency environment.

## Data and frozen selection

113 Git-pinned original files come from Ruff, uv, Helix, mise, Hatch.
Original root licenses/notices, Git blob hashes and source bytes remain preserved.
The final curriculum has 52 families / 1,248 variants.
Original Git commit/tree/blob identities and licenses are preserved. Fixed AST/token validation happens before path-hash bounded selection; candidate rejections are retained. Parser supervision never executes project configuration. A separate 12-family/288-task mixed extension follows actual validation/display review, preserving all 130 original family assignments and initial corpus/run.
Golden, tests and displayed source never enter collection roots. Corpus/Gold /
prepared revisions remain immutable; exact and cross-family copies are audited
before windowing, and 142 source-family assignments are frozen before training.

Prepared snapshot: `78554aa8a7b2f37b3fcc23c098a5388e59e5d118023ff2dbb7b099047afa8c61`. 1361 Gold inputs,
4 exact duplicates merged,
138 cross-family copy documents excluded,
1219 retained. Final Gold accepts 1361 files and
quarantines 0; rejected originals remain retained, never rewritten.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |           76 |        935 |    1164 |
| validation |           10 |        117 |     146 |
| test       |            9 |         72 |     100 |

Full candidate: `artifacts/toml/context512-refine-20261115-01/candidates/epoch-0002.pt`, epoch 2.
SHA-256: `5940c3ef451b3894cb16ec6cbaabaad905c6e59e88930a156882915f7f95dd7e`. Fixed mean per-profile natural validation
role macro F1 (0.9480) selects within its run.
Review precedes freeze and the first adaptive test; no training follows that test.
Source, locks, licenses, every snapshot and full optimizer/RNG experiment remain
under ~/Datasets/neural-semantic-highlighting/toml and artifacts/toml, outside the
committed inference bundle.

## Environment and short training

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**894,872 parameters**: four layers, width 128, four heads, FFN 512, and **512 original
UTF-8 bytes** of context. Smoke precedes short three-epoch phases, initialized from
the compatible full `artifacts/json/context512-mixed-20261111-01/candidates/epoch-0006.pt`. The final refinement raises curriculum batch size from 16 to 64 after observed
multiline errors; natural-source coverage and all data/splits remain unchanged.
All 15 non-smoke epochs take
55.0 seconds; exact invocations, resumptions and timings remain in
reports/experiments.json. Inference .pt/ONNX never initialize or resume training.

No language SDK/interpreter or global dependency is installed. Offline tooling:
Pinned toml-eslint-parser 1.0.3 and eslint-visitor-keys 5.0.1 official npm assets, with original licenses and archive/per-file hashes, using existing Node only. Fixed revisions, original licenses/blob hashes, compiler and binary
provenance are retained. Collected source/dependencies never execute. Parser
acceptance is not project/schema validity. Parser errors, original coverage and Unicode
boundary failures quarantine input. Original CRLF and Unicode text remain unchanged.

## Real and independently visible review

Eight authored displays aggregate **97.73%**.
Ten actual natural validation sources were inspected before freeze; F1 ranges
97.35%–100.00%.
These are visible development diagnostics, not additional unseen test evidence.
Long upstream diagnostic excerpts are bounded in committed reports.

| Display        | Exact-span F1 |
| -------------- | ------------: |
| Cargo.toml     |       100.00% |
| hello.toml     |       100.00% |
| inline.toml    |       100.00% |
| keys.toml      |        91.89% |
| literals.toml  |       100.00% |
| pyproject.toml |       100.00% |
| services.toml  |       100.00% |
| strings.toml   |        68.42% |

The teacher passes 40 separately hand-marked Golden cases and
12 focused tests. Neural spans, roles and modifiers are entirely
exact in **27/40** Golden cases. All eight
examples pass the pinned parser and complete original coverage; no SDK/compiler
execution, dependency compatibility or package API validity is claimed.

Multiline string bodies remain a material weakness: original quoted/hash/shell-looking content can fragment or receive comment/property roles even inside the 512-byte context (strings.toml display 68.42% F1). Quoted keys containing dots can split or acquire the header role (keys.toml 91.89%). Header/assignment roles, dates and long bodies remain approximate. Common 1.0 and tested 1.1 forms do not certify every TOML edge case; the pinned parser labels 1.1 support experimental. No project validation, configuration execution, interpolation or runtime parser/spelling repair is provided. No runtime parser, regular expression or source-spelling
repair masks prediction errors. Browser/native parity and original-text checks
establish consistent execution rather than perfect semantics. This is a bounded
usable baseline; tuning stops after its freeze and first test.
