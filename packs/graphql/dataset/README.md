# GraphQL data

Bounded original query and schema files come from commit/blob-pinned application
and library repositories in `upstreams.json`, with original licenses retained.
`source-selection.json` freezes metadata-only whole application/directory groups
before opening source or predictions; `split-groups.json` retains those splits.
Invalid/unsupported sources are quarantined, and exact, lexical and structural
copies crossing families are excluded by the unchanged shared pipeline.

Sources, licenses and curriculum are retained outside Git under
`~/Datasets/neural-semantic-highlighting/graphql/`. Corpora, Gold and prepared
snapshots are immutable. The original focus curriculum never reads Golden,
Playground examples or held-out source. Nothing is executed or schema-resolved.
Parser sources are hash-pinned in ignored `artifacts/tools/graphql-core-3.3.2`;
no SDK/global dependency installation is required.

    make dataset-graphql
    make test-labeling-graphql

Repository policy remains private. Dataset/source/tool caches and full optimizer
checkpoints stay local; code, contracts, marked fixtures and reviewed inference
bundles follow the existing repository convention. No publishing is performed.
