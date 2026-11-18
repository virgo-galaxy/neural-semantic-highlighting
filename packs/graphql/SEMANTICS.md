# GraphQL source semantics

One standalone byte model covers executable operations and SDL source in `.graphql`
and `.gql`. Input/output use original UTF-8 bytes and UTF-16 half-open spans.
Offline graphql-core 3.3.2 parses syntax only; no schema validation, execution,
network request, resolver or imported document is run. Empty/comment editors are
accepted. The browser/native inference path never imports this parser.

Each lexical token has one role: language words and boolean/null values are
keyword; comments exclude physical line endings; quoted/block strings are one
opaque original string, with escapes unchanged; integers/floats include signs.
Delimiters and insignificant commas/BOM are punctuation. `$`, `@`, `!`, `=`, `&`,
`|` and `...` are operators, separate from identifier names.

AST-local names distinguish fields/aliases/input object keys (property), argument
names (parameter), variable names (variable), operation names (function), fragment
names/spreads (label), directive names (decorator), named type references (type),
enum definitions (enum), and enum values (enum-member). Type/enum/field/input/
argument/operation/fragment/directive definitions carry declaration as applicable;
extension names and references do not. Built-in scalar type references carry
default-library. Enum references use enum-member without global type resolution.
Names such as `query` or `type` used as fields retain their AST-local field role.

No inferred runtime source repair, schema/type resolution or embedded-language
highlighting is provided. Description strings stay strings. Touching neural
string/comment spans may be coalesced without bridging gaps. Context remains
512 bytes; distant definitions and long descriptions can reduce accuracy. The
marked Golden and visible examples are separate from natural held-out source.
