# Zig 0.17.1 dataset

External root: `~/Datasets/neural-semantic-highlighting/zig`; full resumable runs:
`artifacts/zig`. No earlier language corpus/model/experiment is replaced.

`upstreams.json` pins only the official 0.17.1 source archive and individual source
SHA-256s: 96 bounded standard-library files and 64 compiler files, with complete
MIT license. Imports/projects never build or execute. Stdlib/compiler top-level
module families stay intact; original task variants share a directory family.
No old release or master corpus is mixed in. Golden and Playground are excluded.

`make dataset-zig-tools` builds a parse-only native helper with this exact SDK's
`Ast`, `Tokenizer` and primitive metadata. SDK/binary/helper/stdlib hashes are
locked in ignored project cache. The separate official `zig ast-check` validates
source-only errors without type checking, target setup, imports or comptime
execution. No third-party grammar/dependency installation is used.

`make dataset-zig` captures originals, generates current authored tasks, labels
UTF-16, validates full coverage, audits exact/lexical/normalized cross-family
copies and prepares immutable 512-byte snapshots. `split-groups.json` freezes
source/module/task families before training. Unsupported/current structural errors
are quarantined without fallback. Natural/focus/visible evaluation stays separate.
The 42 authored template families were independently checked by Zig 0.17.1 tests
before freezing; current reflection/allocator/errdefer APIs were corrected against
this SDK rather than maintaining previous-version behavior.
