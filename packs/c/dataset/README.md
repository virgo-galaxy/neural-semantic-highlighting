# C dataset

Original bytes, complete licenses, source locks, Gold and prepared snapshots stay
under `~/Datasets/neural-semantic-highlighting/c`. The bounded capture pins curl
8.13.0, Git 2.49.0 and Redis 7.4.2 source/header files in `upstreams.json`.
No upstream project is compiled or executed; headers/includes are not followed.

`make dataset-c-tools` builds Tree-sitter 0.25.10 / C grammar 0.24.1 from fixed
official source blobs using the host compiler. Cache and complete parser licenses
stay in ignored `artifacts/tools/c-gold`. No global SDK or Python/Node package is
installed. `make dataset-c` collects, labels, validates and prepares original source.

Focused tasks cover common C functions, preprocessor directives/macros, structs,
unions, enums, pointers, callbacks, typedefs, strings and modern C constructs.
Variants remain in their original task family. Golden and Playground are excluded.
Invalid syntax, unsupported grammar and uncovered tokens are quarantined. This is
a source-local syntax contract, not preprocessor expansion or project type checking.

Prepare audits exact, lexical and identifier-normalized copies before allocating
intact source/task families. Freeze `split-groups.json` before training; preserve
all snapshots and prior assignments across revisions. Natural and focus evidence
are separate. Full checkpoints live in ignored `artifacts/c`.
