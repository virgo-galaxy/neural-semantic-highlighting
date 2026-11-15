# Dotenv dataset

External data remains under `~/Datasets/neural-semantic-highlighting/dotenv`.
Captures use public example/sample/template filenames at pinned Git commits and
blob identities, with original applicable licenses. No local application .env
files are collected. The Next.js capture uses its bounded examples subtree;
fixed parser/range validation precedes path-hash selection, and rejected
candidates remain recorded and cached. Source/configuration is never executed.

40 assignment-layout families have 24 variants: 960 original files. Plain/export
positions, empty-value positions and duplicate-key layouts are separate families;
string/numeric-looking/URL/quoted/multiline value spellings intentionally share
those families. The linear format's structurally equivalent variants must not
leak across folds by being named as different syntax families. Exact, lexical
and structural copies are audited before windowing; family assignments freeze
before training. Golden, tests and eight display probes are outside collection.

`make dataset-dotenv-tools` verifies the official fixed dotenv 18.0.10 tarball by
SHA512/SHA256 and each extracted file hash, retaining its BSD-2-Clause license.
Existing Node runs `parse()` only; no SDK/global installation, config() call,
environment injection, reference expansion or command execution occurs.
`make dataset-dotenv` creates immutable corpus/Gold/prepared revisions. Continue
only full optimizer/RNG checkpoints under artifacts/dotenv, never inference .pt
or ONNX bundles. Preserve all prior data, captures, runs and formal models.

A bounded 12-family/288-task mixed extension follows observed multiline, quoted
hash and all-string literal errors. Final curriculum: 52 families / 1,248 tasks.
All 52 original family assignments, data revisions and the first six-epoch run
remain preserved; parser semantics and copy-audit policy stay fixed.
