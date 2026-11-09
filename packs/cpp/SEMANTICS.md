# C++ semantic contract

One `cpp` kind for original C++ source and explicitly C++ headers. Extensions are
`.cpp`, `.cc`, `.cxx`, `.c++`, `.C`, `.hpp`, `.hh`, `.hxx`, `.h++`, `.ipp`, `.tpp`.
A shared `.h` filename remains C in automatic extension routing; callers can pass
`language: "cpp"` explicitly for C++ header text. No C/C++ source guessing occurs.

Target common C++11/14/17/20 and accepted modern forms: classes and inheritance,
constructors/destructors, methods/fields, templates/type parameters, namespaces,
aliases/enums, lambdas/captures, structured bindings, range loops, pointers,
references, standard-library call shapes, concepts/requires, directives and macros.
This does not certify every C++23/26 feature, compiler extension or project build.

Gold uses pinned Tree-sitter 0.25.10 / C++ grammar 0.23.4 compiled with the existing
Apple Clang into ignored project cache. The host's existing compiler/SDK compiled
and ran authored programs with C++17/20/23 options. No compiler, SDK, global package
or dependency environment is installed. Collected projects never compile or run;
includes, templates and macros are not instantiated, followed or expanded.

| Source                                                                                                                            | Role                                                                  |
| --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Keywords, primitive/grammar type words, qualifiers, access specifiers                                                             | `keyword`                                                             |
| Original comments                                                                                                                 | `comment`, complete delimiters                                        |
| String/character/raw string literals and include paths                                                                            | `string`, complete original spelling; adjacent literals stay separate |
| Numeric literals                                                                                                                  | `number`                                                              |
| Arithmetic/comparison/assignment, reference/pointer and scope-resolution symbols                                                  | `operator`                                                            |
| Braces, brackets, parentheses, commas, semicolons, dots, ellipsis, template angle delimiters, continuation backslash, initial BOM | `punctuation`                                                         |
| Namespace definitions and qualified scopes                                                                                        | `namespace`                                                           |
| Class / struct, union, typedef, alias and explicit type positions                                                                 | `class` / `type`                                                      |
| Enum tags / constants                                                                                                             | `enum` / `enum-member`                                                |
| Function/method/prototype and function-like macro names                                                                           | `function`                                                            |
| Constructor/destructor names; known type calls                                                                                    | `constructor`                                                         |
| Formal/macro parameters and visible references                                                                                    | `parameter`                                                           |
| Named template type parameters and visible references                                                                             | `type-parameter`                                                      |
| Other local/global names, bindings, init-captures and object-like macros                                                          | `variable`                                                            |
| Fields and member access; selected callable members use `function`                                                                | `property`                                                            |
| Labels / goto targets                                                                                                             | `label`                                                               |
| Accepted attribute names                                                                                                          | `decorator`                                                           |

Definitions carry `declaration`; modifiers are separate predictions. A composite
operator overload name such as `operator+=` and destructor `~Name` is one original
span. User-defined literal suffixes use `function`, separate from their literal.
Type positions preserve locally known class, enum and template-parameter
roles. Known value/parameter callees keep their value role; unknown calls use
`function`. Cross-file/overload/ADL/type inference and dependent-name lookup are
approximate. Namespaces and classes can be ambiguous without project semantics.

The CST exposes macro replacement lists as raw ranges. A bounded scanner labels
only those original ranges offline, with parameter bindings and original markers;
it never substitutes text or repairs runtime predictions. Other directive metadata
is opaque string-like source. Both parseable preprocessor branches remain visible.
Unsupported syntax, missing tokens, uncovered source and invalid coordinates are
quarantined, not completed with another fallback parser.

## Evidence and invariants

- Sorted, nonempty, nonoverlapping original UTF-16 `[start,end)` spans cover every
  non-whitespace character. Preserve original UTF-8 bytes, BOM, CRLF, Unicode,
  astral characters, escapes, raw strings and layout without normalization.
- Source revision/blob/license hashes and complete licenses remain external under
  `~/Datasets/neural-semantic-highlighting/cpp`; parser/compiler/library hashes
  accompany immutable Gold. Offline source never executes.
- Source/module and original task families split before windows, with exact,
  lexical and normalized copy auditing. Freeze family assignments before training
  and preserve them across revisions. Golden and Playground are not collection roots.
- Use short measured training, real natural validation and independent Golden,
  then freeze a candidate before the first adaptive test. Natural/focus/visible
  evidence stay separate. Preserve historical datasets and all existing models.
- Full optimizer/RNG checkpoints live under `artifacts/cpp`. Resume the original
  run's `last.pt`; transfer only from complete compatible training checkpoints.
  Never train from selected inference `.pt` or browser ONNX exports.
- Inference sees original text and learned weights only. No compiler, SDK, parser,
  header resolver, macro expander or source-regex correction is required. The
  unchanged 512-byte context bounds long strings/macros and distant name relations.
