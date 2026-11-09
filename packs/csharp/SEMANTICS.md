# C# semantic contract

One `csharp` document kind for original `.cs` source. The offline teacher uses the
pinned Tree-sitter 0.25.10 C parser and C# grammar 0.23.5, with source-local roles.
It requires no .NET SDK, Mono, CLR, Roslyn or project build. The existing native
compiler builds only the fixed grammar/runtime sources into ignored project cache;
collected C# source is never compiled, loaded or executed.

Coverage targets ordinary classes, structs, interfaces, enums, delegates,
properties/events, generics, attributes, async/await, lambdas, LINQ query syntax,
pattern matching, records/record structs, primary constructors, top-level code,
nullable/reference operators, collection expressions and raw/verbatim/interpolated
strings accepted by this grammar. This is bounded common C# source display, not
certification of every language version. Newer/preview syntax outside the pinned
grammar is quarantined offline. C# script `#r`/`#load`, Razor, XAML, project/solution
XML and bytecode/assemblies are different scopes, not additional C# extensions.

| Source                                                                                     | Role                                                                             |
| ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| Reserved and AST-contextual keywords, builtin type aliases, literals `true`/`false`/`null` | `keyword`                                                                        |
| Line/block/XML documentation comments                                                      | `comment`, complete original delimiters/content                                  |
| Character, ordinary, verbatim, raw, UTF-8 and interpolated string literals                 | `string`, opaque complete original source including prefixes/delimiters/suffixes |
| Numeric literals                                                                           | `number`                                                                         |
| Operators including generics, nullable/conditional tokens, arrows, ranges and pointers     | `operator`                                                                       |
| Braces, parentheses, brackets, dots, commas, semicolons                                    | `punctuation`                                                                    |
| Using, aliases and namespace components                                                    | `namespace`                                                                      |
| Explicit type positions, struct/record-struct/delegate declarations and type parameters    | `type`; declarations carry `declaration`                                         |
| Class/record-class, interface, enum declaration names                                      | `class`, `interface`, `enum` + `declaration`                                     |
| Enum constant declaration and local bare references                                        | `enum-member`; declarations carry `declaration`                                  |
| Constructor/destructor declaration and explicit object-creation type name                  | `constructor`; declaration names carry `declaration`                             |
| Method declaration/call, local/top-level function declaration/reference                    | `method` / `function`; declarations carry `declaration`                          |
| Ordinary/lambda/catch/primary-constructor arguments and local references                   | `parameter`; declarations carry `declaration`                                    |
| Positional record components, fields, properties, events and selected members              | `property`; declarations carry `declaration`                                     |
| Local/loop/resource/query/pattern bindings and local references                            | `variable`; declarations carry `declaration`                                     |
| Attribute type names                                                                       | `decorator`; arguments retain their normal roles                                 |

Named invocation arguments use `parameter`. In an accessor, the implicit `value`
binding uses `parameter` without a declaration span. Primitive aliases stay
keywords. `record`, `var`, `init`, query words and other contextual spellings are
keywords only where recognized by the grammar. Escaped `@identifier` spelling is
retained. A `new()` expression has no fabricated constructor-name span.

Lexical scopes distinguish visible parameters, fields, members, local functions
and bindings without following imports or project references. Unresolved bare
expression names remain `variable`; selected members remain `property` unless an
invocation establishes a callable role. Qualified enum members, overloads,
extension methods, delegate-vs-method references, anonymous member inference,
pattern-flow scope and cross-file names are approximate. There is no framework
API inventory, capital-name guessing, reflection or type checker at inference.

Interpolations stay inside the complete string span. SQL/HTML/JSON/XML contents
are not composed languages. Preprocessor words and symbols are lexical syntax;
no build symbol is evaluated and both parseable branches remain visible. Parser
errors, missing tokens, uncovered source or invalid ranges are quarantined rather
than silently labeled by a fallback lexer.

## Invariants and evidence

- An initial UTF-8 BOM is preserved as original `punctuation`, including its
  original UTF-16 unit. Copy fingerprints ignore this encoding marker only.
- Sorted nonempty nonoverlapping UTF-16 `[start,end)` spans cover each original
  non-whitespace character. Tree byte offsets are mapped through original UTF-8
  characters without normalizing CRLF, Unicode, identifiers or source content.
- Parser, compiler and teacher source/binary identities are recorded with Gold.
  No SDK or global Python/Node package is installed. Offline parser artifacts are
  not imported by local neural inference, browser Workers or consumer packages.
- Immutable source/Gold/prepared revisions stay under the external `csharp`
  dataset root; complete optimizer/RNG checkpoints stay under `artifacts/csharp`.
  Preserve every historical dataset, run and selected model. Never train from
  inference-only `packs/*/model/model.pt` or ONNX exports.
- Source/task families split before byte windows. Exclude exact, lexical and
  identifier-normalized copies across families, freeze assignments before training,
  and keep Golden/Playground out of collection roots. Natural, focus and visible
  development probes remain separate evidence.
- Start with short experiments and measured epoch times. Select using natural
  validation and actual code; freeze before first held-out adaptive test. Never
  use Gold cuts or a source-repair grammar at neural runtime. The same four-layer
  512-byte architecture keeps long literals and distant name roles bounded.
