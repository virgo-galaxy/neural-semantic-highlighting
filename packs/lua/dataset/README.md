# Lua dataset

`make dataset-lua` retains fixed original source, Git blobs and licenses under
`~/Datasets/neural-semantic-highlighting/lua`: Neovim 50 files, Penlight 25,
plenary.nvim 40 and LuaRocks 40. Path-hash selection is bounded to original source
files; Neovim `_meta`/`_test` stubs are excluded. The original curriculum has
52 separate families with 24 variants each. Golden/tests/Playground are excluded.

Corpus, Gold and prepared revisions are immutable. Exact and cross-family copies
are audited before windowing, and source-family assignments freeze before training.
Natural and authored focus streams stay separate. Full optimizer/RNG checkpoints
remain under artifacts/lua, separate from committed inference bundles.

`make dataset-lua-tools` compiles fixed parser sources with existing Clang only in
ignored project cache. Tool revisions, Git blob hashes, licenses and binary/compiler
provenance are retained. Collected source never executes. Syntax/coverage failures
are quarantined and reported without rewriting source.
