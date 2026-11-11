# YAML dataset

External original sources, licenses, Gold and prepared revisions stay under
`~/Datasets/neural-semantic-highlighting/yaml`. Fixed Git commit/tree/blob captures
come from Kubernetes examples, Docker awesome-compose, Prometheus and GitHub
Actions starter workflows. The path-hash selection is bounded to source/configuration
files, excludes test/fixture/generated roots, and reports unsupported candidates.
Source is never executed. Verified project cache bytes can supply the exact same
Git blobs without another network download.

The original curriculum has 45 independent configuration families with 24 variants:
1,080 original files, including mixed CI/Compose/Kubernetes structures, Core
literals, tags, anchors, block headers/bodies, multi-document text and long scalars.
Golden, tests and Playground stay outside collection. Exact/lexical/structural
copies are audited before windowing; source families freeze before training.
Natural and focus evidence remain separate. Every revision/run is preserved.

`make dataset-yaml-tools` verifies and unpacks fixed yaml 2.9.1 npm assets and the
ISC license into ignored project cache using existing Node. Archive and per-file
hashes plus Node/teacher provenance are retained. No SDK, global package, schema
fetch or source/dependency execution is needed. Parser/CST/coverage errors fail
closed. Full optimizer/RNG checkpoints stay under artifacts/yaml, never in formal
inference .pt/ONNX bundles.
