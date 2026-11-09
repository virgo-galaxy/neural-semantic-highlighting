# C semantic contract

One `c` kind for original `.c` and C `.h` source. This is C source display, not
C++ header detection. The host's existing Clang/system C SDK was verified with
small authored C11/C17/C23 compile/run probes; no compiler or environment was
installed. Offline Gold uses pinned Tree-sitter 0.25.10 / C grammar 0.24.1 built
with that existing compiler into ignored project cache. Collected C source and
projects are never built, loaded or executed.

Scope targets common C11/C17, accepted modern/GNU forms, prototypes/functions,
structs/unions/enums, typedefs, arrays/pointers/function pointers, initializers,
labels/goto, preprocessor directives and macros. It does not certify every C23,
compiler extension, build configuration, system header or ABI. Later/unsupported
syntax is quarantined offline. Headers are treated explicitly as C, not guessed
from filename or preprocessor symbols at runtime.

| Source                                                                                                         | Role                                                                  |
| -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Reserved/grammar keywords, primitive aliases, storage/qualifier words                                          | `keyword`                                                             |
| Original line/block comments                                                                                   | `comment`, complete delimiters                                        |
| Character/string literals and include paths                                                                    | `string`, complete original spelling; adjacent literals stay separate |
| Numeric literals                                                                                               | `number`                                                              |
| Arithmetic/assignment/comparison, pointer, ternary and token-pasting symbols                                   | `operator`                                                            |
| Braces, parentheses, brackets, dots, commas, semicolons, ellipsis, line-continuation backslash and initial BOM | `punctuation`                                                         |
| Struct/union tags, typedef names and explicit type positions                                                   | `type`; definitions carry `declaration`                               |
| Enum tag definition / enum constants                                                                           | `enum` / `enum-member`; definitions carry `declaration`               |
| Function/prototype and function-like macro names                                                               | `function`; definitions carry `declaration`                           |
| Formal/function-pointer/macro parameters and visible references                                                | `parameter`; original declarations carry `declaration`                |
| Ordinary local/global names and object-like macros                                                             | `variable`; definitions carry `declaration`                           |
| Struct/union fields and selected members                                                                       | `property`; definitions carry `declaration`                           |
| Label definitions and goto targets                                                                             | `label`; definitions carry `declaration`                              |
| Accepted attribute names                                                                                       | `decorator`                                                           |

Source-local scopes distinguish visible declarations/references, callback names
and ordinary callables without following headers, expanding macros or checking
whole-project types. Known parameter/variable callees keep their value role;
unknown direct calls use `function`. Selected callable fields use `function`.
Type/tag namespaces, complex declarators, extensions, macro-generated names,
external qualifiers and complete symbol resolution remain approximate.

The C CST exposes preprocessor replacement lists as raw ranges. A bounded offline
C-token scanner labels those original bytes, with macro parameter bindings and
original backslashes retained. It never runs cpp, substitutes text or supplies
runtime repairs. Preprocessor conditions are not evaluated; both parseable branches
remain visible. Other directive metadata is opaque string-like source.

## Invariants and evidence

- Sorted nonempty nonoverlapping original UTF-16 `[start,end)` spans cover every
  non-whitespace source character. UTF-8 byte coordinates map through complete
  original characters. Preserve BOM, CRLF, Unicode, escapes and spelling.
- Parser/teacher/tool identities and complete source licenses/hashes accompany
  immutable Gold. Parse errors, missing tokens, unsupported replacement tokens or
  uncovered original characters are quarantined, not guessed into valid labels.
- Data stays under `~/Datasets/neural-semantic-highlighting/c`; full optimizer/RNG
  checkpoints stay under `artifacts/c`. Preserve previous datasets/runs/models.
  Never initialize or resume from inference-only `.pt` or ONNX bundles.
- Source/task families split before windows with exact/lexical/normalized copy
  auditing and frozen assignments. Paired `.c`/`.h` module families stay together.
  Golden and Playground are excluded. Natural and focused evidence stay separate.
- Train in short measured runs, inspect real source and independent Golden, then
  freeze before the first held-out adaptive test. Runtime sees no Gold boundaries,
  parser, SDK, macro evaluator or source-regex correction.
- The existing four-layer, 512-byte architecture keeps long comments/literals,
  macro bodies and distant name relationships bounded. This is a code-display
  engine, not a C compiler, project analyzer or execution-safety checker.
