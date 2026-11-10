# Rust semantic contract

One `rust` kind for original `.rs` source. Target common stable Rust component,
library and script-like snippets: modules/imports, functions/methods, structs and
fields, enums/variants, traits/impls, generics/lifetimes, patterns, closures,
async/await, attributes and macro syntax. Editions 2018, 2021 and 2024 are coverage
targets, not separate models or compiler-version validation. No Cargo manifests,
dependencies, build scripts or procedural macros are loaded or executed.

The host's existing stable Rust toolchain was updated to 1.99.1 before development.
Small authored programs are checked with that compiler and no external crates.
Offline Gold uses pinned Tree-sitter 0.25.10 / Rust grammar 0.24.2, built with the
existing Clang into ignored project cache. Collected library projects never build
or run. This grammar and source-local bindings are not rustc type-checker output.

| Source                                                                                          | Role                                                 |
| ----------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Grammar/reserved keywords, primitives and wildcard `_`                                          | `keyword`                                            |
| Original line, nested block/doc comments and shebang                                            | `comment`, complete spelling                         |
| String/byte/C/raw/character literals                                                            | `string`, including original prefixes and delimiters |
| Numeric literals including suffixes                                                             | `number`                                             |
| Arithmetic/assignment/borrow/comparison, generic angles, `!`, `?`, `:`                          | `operator`                                           |
| Braces/brackets/parentheses, separators, `.`, `::`, `->`, `=>`, range markers, `#`, initial BOM | `punctuation`                                        |
| Modules/use-tree names and unknown qualified scopes                                             | `namespace`                                          |
| Struct/union/alias and explicit type positions, `Self` in type positions                        | `type`                                               |
| Locally known traits / enum tags and variants                                                   | `trait`, `enum`, `enum-member`                       |
| Function/method names and macro names                                                           | `function`; invocation `!` stays separate            |
| Formal/closure parameters and visible references                                                | `parameter`                                          |
| Ordinary local/global names and destructured bindings                                           | `variable`                                           |
| Named struct fields and selected members                                                        | `property`                                           |
| Named type parameters and entire lifetimes such as `'a`                                         | `type-parameter`                                     |
| Attribute names and derive/attribute argument identifiers                                       | `decorator`                                          |
| Entire loop labels such as `'outer`                                                             | `label`                                              |
| `const` and const-generic names                                                                 | `constant`                                           |

Definitions carry `declaration`; modifiers are separate model predictions.
Shorthand field initializers keep their value role; shorthand destructuring fields
are binding declarations. Locally known function/parameter/type/enum names retain
their role; unknown direct/method calls use `function`. Import names stay namespace
roles instead of guessed type information. Trait bounds use known local roles or
ordinary explicit type roles. Lifetimes use `type-parameter`, avoiding an unrelated
language-specific theme role.

Macro token trees are labeled lexically using original CST leaves; metavariables
use `parameter`, fragment names `keyword`. The grammar hides repetition
separators; only recognized punctuation/operator gaps owned by those CST nodes
are recovered offline from original bytes. Unmapped separators are quarantined.
No expansion or procedural execution
occurs. A token tree may contain an arbitrary DSL: inner names do not receive
invented type checking, field or callable resolution. Cross-file types, inferred
variants, method dispatch, borrow checking, captures/shadowing and every newest
stable/nightly extension are not certified. Unsupported/malformed grammar or
uncovered original characters are quarantined, never completed by fallback labels.

## Invariants

Sorted nonempty nonoverlapping UTF-16 `[start,end)` spans cover every non-whitespace
character. Preserve Unicode, BOM, CRLF, escapes, raw strings and source bytes.
Original source/license/blob hashes and parser/compiler hashes accompany immutable
Gold. Data stays under `~/Datasets/neural-semantic-highlighting/rust`; full resumable
optimizer/RNG checkpoints stay under `artifacts/rust`. Preserve earlier language
models, corpora and experiments; never train from inference `.pt` or ONNX bundles.

Natural and focused task families split intact before windows, with exact/lexical/
normalized copy auditing and frozen assignments. Golden and Playground are never
collection roots. Use short measured runs, real validation and independent Golden,
then freeze before first adaptive test. Natural/focus/visible evidence stay separate.
Inference uses the existing small 512-byte model only: no compiler, Cargo, parser,
SDK, macro expander, source-regex repair or source execution is required.
