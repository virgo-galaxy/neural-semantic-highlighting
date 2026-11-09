# Java semantic contract

One `java` document kind for original `.java` source, including `module-info.java`
and `package-info.java`. Offline Gold uses the installed, provenance-pinned JDK 22
compiler scanner and parse-only tree API. It covers ordinary Java 8–22 syntax and
non-preview modern records, sealed types, switch/record patterns, text blocks and
unnamed variables. Later language features and preview syntax are not certified.
Java release numbers do not create separate runtime models or require detection.

| Source                                                                          | Role                                                                        |
| ------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Reserved keywords, literals `true`/`false`/`null`, contextual syntax keywords   | `keyword`                                                                   |
| Original line/block/Javadoc comments                                            | `comment`, including delimiters                                             |
| Character/string literals and complete text blocks                              | `string`, including original delimiters/escapes                             |
| Numeric literals                                                                | `number`                                                                    |
| Arithmetic, assignment, comparisons, generic angle tokens, `->`, `::`, `?`, `:` | `operator`                                                                  |
| Braces, parentheses, brackets, dots, commas, semicolons, `@`, ellipsis          | `punctuation`                                                               |
| Package/import/module path components                                           | `namespace`; static import terminal names are also namespace                |
| Type positions and type parameter names                                         | `type`; type parameter declarations carry `declaration`                     |
| Class/record, interface/annotation type, enum declaration names                 | `class`, `interface`, `enum` + `declaration`                                |
| Enum constant declarations and source-local references                          | `enum-member`; declarations carry `declaration`                             |
| Constructor declaration/new-expression type name                                | `constructor`; declaration names carry `declaration`; `new` remains keyword |
| Method declaration, call or method-reference name                               | `method`; declaration names carry `declaration`                             |
| Method/lambda/catch formal arguments and their local references                 | `parameter`; declarations carry `declaration`                               |
| Local, loop, resource and pattern binding names/references                      | `variable`; declarations carry `declaration`                                |
| Fields/record components and member selections                                  | `property`; declarations carry `declaration`                                |
| Annotation type name components                                                 | `decorator`                                                                 |

Primitive type words and `void` remain keywords. `var`, `record`, `yield`, `sealed`,
`permits`, `when` and module words become keywords only in relevant AST positions;
ordinary identifiers with those spellings retain their local role. `non-sealed`
retains three lexical spans: keyword, operator, keyword. `_` is a keyword.

Source-local lexical scopes distinguish parameters, fields, methods and local
bindings without resolving imports or external dependencies. Types in type
positions remain `type` even when declared as a class/interface/enum elsewhere.
Unknown bare expression names are `variable`; selected members are `property`
unless a method call/reference establishes `method`. Qualifier types, cross-file
symbols, overloads, pattern flow scope and framework semantics are not fully
resolved. Annotations are not executed; annotation processors are disabled.

## Invariants and evaluation

- Sorted nonempty nonoverlapping original UTF-16 `[start,end)` spans, aligned to
  Unicode character boundaries. Scanner/AST coordinates refer to original source,
  including Unicode escapes, CRLF and supplementary characters.
- All non-whitespace source units receive Gold roles. Javac lexical/parse errors
  are quarantined; no source is compiled, loaded, imported or executed to label it.
  Comments and strings retain complete compiler-scanned regions. String contents,
  Javadoc tags, SQL/HTML templates and foreign DSLs are not recursively parsed.
- Runtime accepts complete files and displayed snippets. The initial offline
  corpus uses complete parseable files. Unsupported incomplete syntax is not
  guessed into a successful Gold record. A scanner-only trailing newline captures
  EOF line comments and never enters returned spans or stored source bytes.
- Immutable corpora/Gold/prepared snapshots stay under the external Java dataset;
  full optimizer/RNG checkpoints stay under `artifacts/java`. Never train from an
  inference-only `packs/*/model/model.pt` file.
- Exact, lexical and identifier-normalized copies crossing families are excluded.
  Freeze source-family splits before training. Golden and Playground are excluded
  from collection. Natural and focused results remain separate.
- Validation/test and inference use predicted boundaries, never Gold cursor cuts.
  Select with natural validation, inspect real code/Golden, freeze the candidate,
  then evaluate independent test once. Document small holdouts and real failures.
- Browser and local inference use only original text and learned weights. JDK,
  offline teacher, grammar heuristics and source repairs are absent at runtime.
  The 512-byte context limits distant bindings and long comments/text blocks.
