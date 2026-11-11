# JSON / JSONC dataset

External source, Gold and prepared snapshots stay under
`~/Datasets/neural-semantic-highlighting/json`. Pinned real configurations/data
come from Microsoft VS Code, vscode-extension-samples, TypeScript and Zed.
Original files, Git blobs, licenses and a syntax-based profile inventory are
retained. Only candidates accepted by the fixed JSON/JSONC contract are selected;
this is not a claim that other upstream formats are invalid.

The original curriculum has 40 shared families with 24 variants per profile:
1,920 files, including manifests/configuration, schemas/API data, strings/numbers,
comments, trailing commas, mixed structures and long literals. JSON and JSONC
variants of a family share one source-group identity; they cannot cross folds.
Real files share directory families across profiles. Exact, lexical and structural
copy auditing runs before windowing without exemptions for these formats.
Golden, tests and Playground sources never enter collection roots.

`make dataset-json-tools` unpacks the fixed official jsonc-parser 3.3.1 npm archive
into ignored project cache after SHA-512/SHA-256 and per-file checks. Its MIT license
and Node/labeler hashes remain recorded. No npm install, SDK, schema fetching or
execution of collected scripts/configuration is involved. The parser's recovery
errors and incomplete original coverage fail closed. Revisions are immutable;
full optimizer/RNG checkpoints stay under artifacts/json, separate from inference
.pt/ONNX bundles. Preserve all prior language data, experiments and formal models.

A separate mixed extension adds 12 shared families / 576 files for escaped and
embedded-looking string contents, paths, quoted keys and mixed block comments.
It follows the same copy audit after the initial review found entire simple-string
families excluded as structural copies. The original curriculum, snapshots and
159 frozen assignments remain preserved; the audit policy is unchanged.
