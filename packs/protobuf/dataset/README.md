# Protocol Buffers data

Commit/blob-pinned `.proto` files are bounded from five application/library
repositories in `upstreams.json`; original bytes and licenses are preserved.
`source-selection.json` fixes metadata-only whole directory/package families
before opening source or predictions. The final v2 selection uses production API
definitions only and reserves 12 fresh Temporal API files for independent test.
The original filter missed mixed-case upstream test directories; those sources
remain archived under the initial history and are removed from formal natural
data. The v2 audit also compares fresh tests against earlier non-test fingerprints. `split-groups.json` retains these splits.
The unchanged shared pipeline excludes exact, lexical and shape copies crossing
families. Unsupported/invalid syntax is quarantined, never silently repaired.

External root: `~/Datasets/neural-semantic-highlighting/protobuf/`. Sources,
licenses, original authored curriculum, corpus/Gold and prepared snapshots remain
local and immutable. Full training checkpoints stay under `artifacts/protobuf`.
No Golden, display or held-out text is read by the curriculum generator.

    make dataset-protobuf
    make test-labeling-protobuf

Existing Clang builds a commit/blob-pinned Tree-sitter source-only parser under
ignored `artifacts/tools/protobuf-gold`. It never loads imports, executes sources,
resolves symbols or generates code. No SDK or global installation is needed.
The repository and inference bundles follow existing private distribution policy;
no source-data upload, npm publication or visibility change is performed.
