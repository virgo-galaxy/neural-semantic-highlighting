# Zig 0.17.1 semantic contract

One `zig` entry for original `.zig` programming source, targeting **Zig 0.17.1
only**. Current syntax and standard-library usage are the goal. Historical Zig
API/grammar compatibility and development/master snapshots are not targets.
ZON/file-format support is a separate scope, not part of this pack.

Gold uses this exact official SDK's `std.zig.Ast`, `Tokenizer`, primitive metadata
and `zig ast-check`. The native helper parses only original bytes and emits AST
metadata; `ast-check` validates errors decidable from source without target/type
checking. Neither follows imports, evaluates comptime code, embeds files, compiles
input projects or executes source. No third-party historical grammar chooses labels.
Natural source comes only from the SHA-256-pinned official 0.17.1 release archive.
Only authored stand-alone examples/probes are compiled/tested with this SDK.

| Source                                                               | Role                   |
| -------------------------------------------------------------------- | ---------------------- |
| Official keyword tokens, primitive type/value names and `_`          | `keyword`              |
| Line/doc/container-doc comments                                      | `comment`              |
| Quoted/character literals and each original multiline-string line    | `string`               |
| Numeric literals                                                     | `number`               |
| Operators, optional/error markers and capture pipes                  | `operator`             |
| Delimiters/separators, `.`, `:`, `..`, `...`, `=>` and initial BOM   | `punctuation`          |
| Explicit `@import`-based bindings and their local references         | `namespace`            |
| Struct/union/opaque/error-set bindings and explicit type positions   | `type`                 |
| Enum bindings / enum literal, error and enum-member names            | `enum` / `enum-member` |
| Named functions, unknown syntactic calls and entire `@builtin` names | `function`             |
| Formal names and local references                                    | `parameter`            |
| `comptime T: type` formal names and references                       | `type-parameter`       |
| Other local `const`/`var` and capture bindings                       | `variable`             |
| Container fields, struct initializer fields and selected members     | `property`             |
| Other container-level `const` bindings                               | `constant`             |
| Loop/block labels and break/continue targets                         | `label`                |

Declarations carry `declaration`. AST ranges scope parameters, block locals,
container declarations and payloads. Quoted `@"name"` identifiers keep their full
original spelling. Type expressions and directly visible container/import forms
provide local syntax roles; no capitalization heuristic invents types. Inferred
aliases, type-producing functions, method dispatch, shadowing, quoted-name aliasing
and dependency symbols remain approximate. Current standard-library member
compatibility is not established by parsing arbitrary third-party code.

The official tokenizer omits ordinary line comments. Only whitespace or complete
`//` comments in uncovered gaps between official tokens are accepted; strings and
quoted identifiers are never rescanned. Unknown gaps, current `ast-check` errors,
invalid tokens and malformed UTF-16 coverage fail closed and are quarantined.
No fallback parser fabricates labels for older syntax.

Sorted nonempty nonoverlapping original UTF-16 `[start,end)` spans cover all
non-whitespace characters. Preserve BOM, CRLF, Unicode, escapes and literal bytes.
Parser/compiler/stdlib/helper hashes and full release licenses accompany immutable
Gold. Data stays under `~/Datasets/neural-semantic-highlighting/zig`; complete
optimizer/RNG checkpoints under `artifacts/zig`. Preserve all earlier datasets,
experiments and models; initialize/resume only full training checkpoints.

Current source/module and task families split intact before windows, with exact,
lexical and normalized copy auditing and frozen assignments. Golden and Playground
are never collected. Short runs, real validation and independent Golden precede
candidate freeze and first adaptive test. Natural/focus/visible scores stay
separate. Runtime uses learned weights only: no Zig SDK, parser, source-regex
repair, Gold cuts, imports or comptime execution. The existing 512-byte context
bounds long literals/comments and distant symbol information.
