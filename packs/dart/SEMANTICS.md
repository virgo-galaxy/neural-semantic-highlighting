# Dart semantic contract

One entry for original .dart source, including ordinary Flutter widget code.
Common null-safe Dart and accepted modern forms share one model. Records,
patterns, class modifiers, extension types, null-aware elements, dot shorthands
and primary constructors have bounded parse probes, without a claim of complete
SDK-version compatibility. No Dart or Flutter SDK is installed or used.

Gold uses Tree-sitter 0.25.10 and nielsenko/tree-sitter-dart 0.3.0 at commit
cc75f92b34037bcdbc05b12b0db7fe20677306c1. Original generated C parser, scanner,
node metadata, licenses and Git blobs are pinned. Existing Clang builds only the
project-local parser. This independent CST/source-local teacher is not the
official analyzer/compiler. Labeling never follows imports/configuration,
builds, executes source, runs generators or fetches an SDK. Missing/error syntax,
unmapped leaves and incomplete original-text coverage fail closed.

| Source                                                                                          | Role               |
| ----------------------------------------------------------------------------------------------- | ------------------ |
| Keyword syntax, void/dynamic/null/boolean values and modern wildcard bindings                   | keyword            |
| Ordinary, nested block and documentation comments                                               | comment            |
| Whole plain/raw/multiline strings and symbol literals; interpolated text segments               | string             |
| Integer, hex and floating-point literals                                                        | number             |
| Expression operators and interpolation dollar sign                                              | operator           |
| Brackets, separators, annotation marker, interpolation braces, arrow and BOM                    | punctuation        |
| Explicit import aliases, show/hide names and qualified type prefixes                            | namespace          |
| Classes/mixins/extensions/type aliases and explicit type positions                              | type               |
| Enum declarations / locally known enum entries                                                  | enum / enum-member |
| Top-level/local functions and unresolved syntactic calls                                        | function           |
| Declared methods and syntactic member calls                                                     | method             |
| Constructor declarations, explicit new/const construction and known local type calls            | constructor        |
| Formal arguments, catch payloads, local references and named argument labels                    | parameter          |
| Other variable/pattern bindings and local references                                            | variable           |
| Fields/getters/setters, initializing formals, primary fields, record names and member selection | property           |
| Generic parameter declarations/references                                                       | type-parameter     |
| Annotation names, without executing annotations                                                 | decorator          |
| Explicit const bindings                                                                         | constant           |
| Statement labels and break/continue targets                                                     | label              |

Declarations carry the declaration modifier. AST ranges scope containers,
callable bodies, blocks, loop/pattern branches and catches. Generic names are
visible in return types. Modern underscore local/formal wildcards do not bind.
Inference, overloads, imported constructors/widgets, extension dispatch, generated
members, field/parameter distinction and complex pattern scopes remain approximate.
Unknown Widget(...) syntax is a function call without invented capitalization or
package knowledge. Explicit construction and locally declared types provide
stronger constructor evidence. Named argument labels remain parameters.

Plain/raw strings stay whole; interpolated segments merge only contiguous original
string leaves. Expressions inside interpolation use normal CST roles; raw text is
never rescanned for interpolation/comments. No newline rewriting, detabbing,
delimiter reconstruction or lexing fallback fabricates source. Sorted nonempty,
nonoverlapping original UTF-16 [start,end) spans cover every non-whitespace
character, retaining Unicode, BOM, CRLF and escapes.

Original bounded Dart package and stable Flutter sources/licenses are pinned
outside the repository. Intact package/module/task families split before windows,
with exact/lexical/normalized copy auditing and frozen assignments. Golden and
Playground are excluded. Short measured runs and actual validation review precede
candidate freeze and first adaptive test. Natural/focus/visible evidence stays
separate. Data remains under ~/Datasets/neural-semantic-highlighting/dart;
full resumable optimizer/RNG checkpoints under artifacts/dart. Preserve all
previous data/runs/models and initialize/resume only full training checkpoints.

Runtime uses the original 512-byte architecture and learned weights only: no
Dart/Flutter SDK, language parser/analyzer, source-regex repair, Gold cuts, project
dependencies or execution. The context bounds distant names and long literals.
Browser conversion parity does not establish semantic accuracy.
