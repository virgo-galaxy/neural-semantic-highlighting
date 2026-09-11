# Go Pack Semantic Contract

This document defines the semantic-labeling contract for the Go language pack.

## Principle

The highlighting layer labels the **local semantic role of the source span at its current position**.

The Go pack reuses the common NSH semantic vocabulary wherever that vocabulary already expresses the language accurately. It does not introduce Go-specific token types merely to mirror Go AST node names.

```go
type Server struct {
    name string
}

func (s *Server) Start(ctx context.Context) error {
    go s.run(ctx)
    return nil
}
```

- `Server` in the type declaration: `type` + `declaration`
- `name`: `property` + `declaration`
- `string`: `type` + `default-library`
- `s` in the receiver: `parameter` + `declaration`
- `Start`: `method` + `declaration`
- `ctx` in the parameter list: `parameter` + `declaration`
- `context`: `namespace`
- `Context`: `type`
- `error`: `type` + `default-library`
- `go`: `keyword`
- `s` in `s.run`: `variable`
- `run`: `method`
- `ctx` in the call: `variable`
- `nil`: `variable` + `readonly` + `default-library`

The fact that a reference resolves to a parameter, field, package declaration, or named type belongs to symbol identity rather than semantic highlighting unless that information changes the local role of the source span.

## Document kind

The initial Go pack supports one document kind:

| Document kind | Extensions |
| ------------- | ---------- |
| `go`          | `.go`      |

Generated files, build-tag variants, tests, platform-specific files, and command/package layouts remain the same document kind. File naming conventions do not create separate semantic document kinds.

## Lexical roles

| Source role                | Token type    |
| -------------------------- | ------------- |
| Go keyword                 | `keyword`     |
| line or block comment      | `comment`     |
| interpreted string literal | `string`      |
| raw string literal         | `string`      |
| rune literal               | `string`      |
| integer literal            | `number`      |
| floating-point literal     | `number`      |
| imaginary literal          | `number`      |
| operator                   | `operator`    |
| punctuation / delimiter    | `punctuation` |

Import paths remain `string`.

Rune literals use `string` because the common NSH vocabulary intentionally does not introduce a separate character-literal token type.

## Declaration roles

Declaration sites keep the most specific common semantic role that accurately describes the Go construct.

| Source role                        | Token type       | Required modifiers        |
| ---------------------------------- | ---------------- | ------------------------- |
| package clause name                | `namespace`      | `declaration`             |
| explicit import alias              | `namespace`      | `declaration`             |
| named type declaration             | `type`           | `declaration`             |
| named interface declaration        | `interface`      | `declaration`             |
| type parameter declaration         | `type-parameter` | `declaration`             |
| package-level function declaration | `function`       | `declaration`             |
| method declaration                 | `method`         | `declaration`             |
| interface method declaration       | `method`         | `declaration`             |
| receiver name                      | `parameter`      | `declaration`             |
| function or method parameter       | `parameter`      | `declaration`             |
| named result parameter             | `parameter`      | `declaration`             |
| variable declaration               | `variable`       | `declaration`             |
| short variable declaration binding | `variable`       | `declaration`             |
| range variable declaration binding | `variable`       | `declaration`             |
| constant declaration               | `variable`       | `declaration`, `readonly` |
| struct field declaration           | `property`       | `declaration`             |
| label declaration                  | `label`          | `declaration`             |

A named struct type is `type`, not `class`. Go does not use the `class` semantic role.

A named interface declaration may use `interface` at its declaration site. References to that interface use `type`, matching the local-role principle.

The blank identifier `_` does not create a binding. At value/binding positions it is treated as `variable` without the `declaration` modifier.

## Reference roles

Reference sites are classified by the role visible at the reference location.

| Reference shape                                                         | Token type  |
| ----------------------------------------------------------------------- | ----------- |
| ordinary value identifier                                               | `variable`  |
| identifier used as a direct function call target                        | `function`  |
| method selected on a value and called                                   | `method`    |
| struct field selector                                                   | `property`  |
| package qualifier in a selector                                         | `namespace` |
| package-level function selected through a package qualifier             | `function`  |
| package-level variable or constant selected through a package qualifier | `variable`  |
| identifier in a type position                                           | `type`      |
| imported type selected through a package qualifier                      | `type`      |
| type parameter reference                                                | `type`      |
| struct literal keyed field                                              | `property`  |
| label reference in `break`, `continue`, or `goto`                       | `label`     |

Examples:

```go
fmt.Println(user.Name)
```

- `fmt`: `namespace`
- `Println`: `function`
- `user`: `variable`
- `Name`: `property`

```go
client.Do(req)
```

- `client`: `variable`
- `Do`: `method`
- `req`: `variable`

```go
var client http.Client
```

- `client`: `variable` + `declaration`
- `http`: `namespace`
- `Client`: `type`

## Built-in and predeclared identifiers

The `default-library` modifier marks Go predeclared language/library identifiers when their local semantic role is known.

Examples include:

| Source role                                                                                                                 | Token type | Modifiers                     |
| --------------------------------------------------------------------------------------------------------------------------- | ---------- | ----------------------------- |
| `string`, `int`, `bool`, `error`, `any`, `comparable`                                                                       | `type`     | `default-library`             |
| `len`, `cap`, `make`, `new`, `append`, `copy`, `delete`, `close`, `panic`, `recover`, `complex`, `real`, `imag` when called | `function` | `default-library`             |
| `true`, `false`, `iota`, `nil`                                                                                              | `variable` | `readonly`, `default-library` |

These identifiers are not reclassified as keywords merely because they are built into the language.

## Interfaces and methods

Go interfaces do not introduce a separate reference role for interface values.

```go
type Reader interface {
    Read(p []byte) (int, error)
}
```

- `Reader`: `interface` + `declaration`
- `Read`: `method` + `declaration`
- `p`: `parameter` + `declaration`
- `byte`, `int`, `error`: `type` + `default-library`

A method reference remains `method` whether the receiver's concrete type is known statically or through an interface.

## Generics

Type parameter declarations use `type-parameter` + `declaration`.

References to type parameters use `type`.

```go
func Map[T any, R any](items []T, fn func(T) R) []R
```

- `Map`: `function` + `declaration`
- `T`, `R` in the type parameter list: `type-parameter` + `declaration`
- `any`: `type` + `default-library`
- later uses of `T` and `R`: `type`
- `items`, `fn`: `parameter` + `declaration`

The semantic layer does not need a separate token type for generic instantiation.

## Visibility

Go's exported/unexported convention is based on identifier capitalization.

The initial Go pack does **not** map capitalization to the `public` or `private` modifiers. Visibility is intentionally excluded from the first semantic contract because it would add modifiers to a large fraction of identifiers without changing their primary highlighting role.

This may be revisited only if real product usage shows that visibility is useful as a semantic-highlighting modifier.

## Embedded fields

Embedded fields do not receive an invented property span when the source does not contain a separate field-name token.

```go
type Server struct {
    http.Server
}
```

- `http`: `namespace`
- `Server`: `type`

The implicit promoted field identity belongs to symbol intelligence, not to a synthetic highlighting span.

## Struct tags

Struct tags are an explicit Go-core coverage requirement. A tag is the optional string literal
following a struct field declaration; it is not restricted by the Go grammar to backticks or to
any particular metadata key.

```go
type Record struct {
    ID   int64  `json:"id" gorm:"primaryKey;column:id"`
    Name string `json:"name,omitempty" binding:"required"`
    Note string "json:\"note,omitempty\""
}
```

Each tag is one complete `string` span, including its opening and closing literal delimiters.
The first model does not split keys, colons, escaped quotes, comma options, semicolon-separated
values, or framework-specific content into separate spans. The renderer chooses the theme's
string color; the semantic pack does not prescribe green or any other color.

The `key:"value"` format is the conventional format interpreted by `reflect.StructTag`, not an
additional restriction on Go string-literal syntax. Unknown keys and free-form tag strings remain
strings. Raw and interpreted literals, multiple entries, empty tags, escapes, non-ASCII text,
and tags on fields whose types are anonymous structs all require boundary coverage.

JSON, XML, YAML, database, validation, and ORM metadata may occur in fixtures and training inputs.
Their presence does not imply that the Go core pack interprets a framework's internal metadata
language. No new public token types or modifiers are introduced for these conventions.

## Comments, directives, and reflection

Line comments, block comments, package/type/function documentation, build constraints,
`//go:generate`, and other `//go:*` directives keep the `comment` role. The tag or directive text
must not escape its enclosing string or comment span and become an ordinary Go identifier.

Gold labeling reads source; it does not execute generators, follow doc links, evaluate directives,
or resolve a reflection call's runtime result. Ordinary calls and selectors involving `reflect`
use the same namespace, function, method, property, and type rules as other Go code.

Exact source offsets must be preserved even when the Go scanner normalizes carriage returns in a
raw string or comment. CRLF input is not a reason to truncate a closing quote or comment delimiter.

## Boundary semantics

Semantic roles do not expand lexical boundaries.

Strings, comments, rune literals, numbers, operators, punctuation, identifiers, and selectors retain their exact source spans.

The model input remains raw UTF-8 bytes. Runtime output offsets follow the pack/runtime contract rather than byte offsets exposed directly to consumers.

## Initial modifier scope

The first Go pack intentionally uses a small modifier set:

- `declaration`
- `readonly`
- `default-library`

The following existing NSH modifiers are not used merely because they exist in another language pack:

- `static`
- `async`
- `generator`
- `abstract`
- `public`
- `protected`
- `private`
- `optional`
- `getter`
- `setter`

New modifiers should be added only when a real Go semantic distinction cannot be represented accurately by the existing vocabulary and the distinction materially helps highlighting.

## Out of scope for the first Go pack

The first semantic-highlighting model does not require:

- cross-file symbol identity;
- rename/find-references behavior;
- package graph analysis as a product feature;
- framework-specific semantics;
- build-system semantics;
- cgo-specific domain semantics;
- generated-code provenance;
- linter/static-analysis diagnostics;
- exported/unexported visualization;
- doc-link resolution.

The Go labeler may use compiler/type-checker information to create high-quality Gold labels without exposing those capabilities as part of the runtime highlighting contract.

## Layer boundary

Semantic highlighting answers:

> What role does this span play here?

A future symbol-intelligence layer may answer:

> Which declaration does this reference resolve to?

That future layer may provide symbol identity, declaration location, package relationships, find-references, rename, and project-level relationships. Those capabilities are not required by this highlighting contract.
