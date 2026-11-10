# Rust dataset

External root: `~/Datasets/neural-semantic-highlighting/rust`. Full resumable
checkpoints and experiments remain under ignored `artifacts/rust`.

`upstreams.json` pins bounded Serde, Tokio and Regex library sources, Git blobs
and complete licenses. Projects are read, never built/executed; imports and Cargo
manifests/build scripts/dependencies are never followed. Original curriculum
variants stay in one task family. Golden and Playground are excluded.

`make dataset-rust-tools` builds the pinned offline Tree-sitter runtime/grammar
with existing Clang in project cache, with source/compiler/library identity locks.
No Cargo/npm/Python dependency or new language environment is installed. The
existing stable Rust toolchain was explicitly updated at the user's request;
authored, crate-free compiler probes are separate from offline grammar labels.

`make dataset-rust` captures source, generates original tasks, publishes immutable
Gold and prepares 512-byte snapshots. Exact/lexical/normalized cross-family copies
are excluded before windows. `split-groups.json` freezes intact source/task-family
assignments before training. Unknown grammar/coverage is quarantined with identity,
never fabricated into a valid label. Natural and focus scores remain separate.

The literal revision adds 512 original raw/byte/C-string and format-string context
tasks across 16 intact families. It is motivated by visible validation failures,
not held-out test scores. The original 192 frozen assignments are preserved and
extended before this revision trains. Previous snapshots and runs are retained;
copy-exclusion rules remain unchanged.
