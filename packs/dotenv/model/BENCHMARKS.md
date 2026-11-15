# .env baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Role macro F1
averages represented roles; declaration modifiers are separate. It measures
independently checked original dotenv ranges and source-local roles, not application
schema validity, configuration execution, template execution or syntax validation
by the runtime highlighter.

| Evidence   | Profile | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | ------- | ------- | --------: | ------------: | ------------: |
| Validation | dotenv  | natural |         3 |        97.14% |        97.19% |
| Validation | dotenv  | focus   |       168 |        91.20% |        77.76% |
| First test | dotenv  | natural |         3 |        98.25% |        93.73% |
| First test | dotenv  | focus   |        96 |        96.79% |        80.37% |

Natural test aggregate: **98.25%** across
3 real files. Focus and combined-corpus scores
must not be presented as real-code accuracy. Small family holdouts from bounded
captures do not certify an entire language ecosystem or dependency environment.

## Data and frozen selection

56 Git-pinned original files come from Next.js, Supabase, Laravel application skeleton, Chatwoot, Outline.
Original root licenses/notices, Git blob hashes and source bytes remain preserved.
The final curriculum has 52 families / 1248 variants.
Public example/sample/template files and applicable licenses are retained with exact Git commit/tree/blob identities. No local application .env files are read. Fixed parse-only independent key/value and source-range validation precedes bounded selection; rejections are retained. Equivalent value spellings stay in the same structural family. Laravel retains its original README/composer MIT license declarations because that skeleton has no standalone LICENSE file. A separate 12-family/288-task mixed extension follows observed multiline/hash/literal errors, preserving all 52 original family assignments and the initial six-epoch run.
Golden, tests and displayed source never enter collection roots. Corpus/Gold /
prepared revisions remain immutable; exact and cross-family copies are audited
before windowing, and 64 source-family assignments are frozen before training.

Prepared snapshot: `8c6aa016bf8ec8410dca52a1736e73f63848f0f1169873bc4c645731fd96be5b`. 1304 Gold inputs,
4 exact duplicates merged,
131 cross-family copy documents excluded,
1169 retained. Final Gold accepts 1304 files and
quarantines 0; rejected originals remain retained, never rewritten.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |           11 |        888 |     958 |
| validation |            3 |        168 |     176 |
| test       |            3 |         96 |     104 |

Full candidate: `artifacts/dotenv/context512-refine-20261116-01/candidates/epoch-0003.pt`, epoch 3.
SHA-256: `afc09e35b616f3923338ce2718356c949297e3534279738fe8c9588c31e11542`. Fixed mean per-profile natural validation
role macro F1 (0.9522) selects within its run.
Selection is phase-local. The final refinement epochs tie on fixed natural
validation score; the later full candidate is kept for its better visible
quote/multiline results. It does not maximize a score across all prior phases.
Review precedes freeze and the first adaptive test; no training follows that test.
Source, locks, licenses, every snapshot and full optimizer/RNG experiment remain
under ~/Datasets/neural-semantic-highlighting/dotenv and artifacts/dotenv, outside the
committed inference bundle.

## Environment and short training

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**894,872 parameters**: four layers, width 128, four heads, FFN 512, and **512 original
UTF-8 bytes** of context. Smoke precedes short three-epoch phases, initialized from
the compatible full `artifacts/ini/context512-refine-20261115-01/candidates/epoch-0002.pt`. Exact batch sizes, learning rates and phase budgets remain in the experiment
record; each phase preserves full natural-source coverage.
All 15 non-smoke epochs take
37.6 seconds; exact invocations, resumptions and timings remain in
reports/experiments.json. Inference .pt/ONNX never initialize or resume training.

No language SDK/interpreter or global dependency is installed. Offline tooling:
Pinned official dotenv 18.0.10 parse-only npm assets with retained BSD-2-Clause license and archive/per-file hashes, using existing Node only. Fixed revisions, original licenses/blob hashes, compiler and binary
provenance are retained. Collected source/dependencies never execute. Parser
acceptance is not application/dialect validity. Parser errors, original coverage and Unicode
boundary failures quarantine input. Original CRLF and Unicode text remain unchanged.

## Real and independently visible review

Eight authored displays aggregate **97.70%**.
3 actual natural validation sources were inspected before freeze; F1 ranges
95.08%–100.00%.
These are visible development diagnostics, not additional unseen test evidence.
Long upstream diagnostic excerpts are bounded in committed reports.

| Display        | Exact-span F1 |
| -------------- | ------------: |
| comments.env   |        93.33% |
| export.env     |       100.00% |
| frontend.env   |       100.00% |
| hello.env      |       100.00% |
| multiline.env  |        81.82% |
| production.env |       100.00% |
| quotes.env     |       100.00% |
| references.env |       100.00% |

The teacher passes 40 separately hand-marked Golden cases and
12 focused tests. Neural spans, roles and modifiers are entirely
exact in **21/40** Golden cases. All eight
examples pass the recorded offline teacher and complete original coverage; no SDK/compiler
execution, dependency compatibility or package API validity is claimed.

Quoted/multiline boundaries remain a measured weakness (multiline.env display 81.82% F1), including assignment/hash-looking content within values; individual comment/value boundaries can still split (comments.env 93.33%). Declaration flags, escaped quotes and long bodies remain approximate. One common ASCII-name/equals-assignment dotenv profile is supported; loader-specific colon/dotted/dashed names are outside the teacher contract. All values remain strings. No expansion, command substitution, environment injection, decryption, application validation or runtime parser/spelling repair is provided. No runtime parser, regular expression or source-spelling
repair masks prediction errors. Browser/native parity and original-text checks
establish consistent execution rather than perfect semantics. This is a bounded
usable baseline; tuning stops after its freeze and first test.
