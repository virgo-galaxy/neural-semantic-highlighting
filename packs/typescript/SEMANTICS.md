# TypeScript Pack Semantic Contract

This document defines the semantic-labeling contract used by the TypeScript family pack for JavaScript, TypeScript, JSX, and TSX.

## Principle

The highlighting layer labels the **local semantic role of the source span at its current position**.

It does not require a reference to preserve the declaration-kind identity of the symbol it resolves to.

```ts
function render(token: ThemeToken) {
  return token.colorText;
}
```

- `token` in the parameter list: `parameter` + `declaration`
- `ThemeToken` in the annotation: `type`
- `token` in `token.colorText`: `variable`
- `colorText`: `property`

```ts
interface User {}
const user: User = value;
```

- `User` in the interface declaration: `interface` + `declaration`
- `User` in the type annotation: `type`

The fact that a `variable` reference resolves to a parameter declaration, or that a `type` reference resolves to an interface declaration, belongs to a future symbol-identity layer rather than semantic highlighting.

## Declaration roles

Declaration sites keep the most specific supported declaration kind.

| Source role | Token type | Required modifier |
| --- | --- | --- |
| class declaration name | `class` | `declaration` |
| interface declaration name | `interface` | `declaration` |
| enum declaration name | `enum` | `declaration` |
| enum member declaration name | `enum-member` | `declaration` |
| type alias declaration name | `type` | `declaration` |
| type parameter declaration name | `type-parameter` | `declaration` |
| function declaration name | `function` | `declaration` |
| method declaration/signature name | `method` | `declaration` |
| constructor keyword | `constructor` | `declaration` |
| parameter declaration/binding | `parameter` | `declaration` |
| variable declaration/binding | `variable` | `declaration` |
| property declaration/signature | `property` | `declaration` |
| namespace declaration/import binding | `namespace` | `declaration` |
| value import binding | `variable` | `declaration` |
| type-only import binding | `type` | `declaration` |

Existing semantic modifiers such as `readonly`, `static`, `async`, `generator`, `abstract`, `public`, `protected`, `private`, `optional`, `getter`, and `setter` remain orthogonal to this rule.

## Reference roles

Reference sites are classified by the role visible at the reference location.

| Reference shape | Token type |
| --- | --- |
| ordinary value identifier | `variable` |
| identifier used as a direct call target, `fn()` | `function` |
| member used as a direct call target, `obj.run()` | `method` |
| non-call member access, `obj.value` | `property` |
| identifier used as a `new` target, `new Foo()` | `class` |
| identifier in a type-reference position | `type` |
| right side of a qualified type, `NS.User` | `type` |
| namespace side of a qualified type, `NS.User` | `namespace` |
| type-only export specifier | `type` |
| ordinary export specifier | `variable` |
| decorator identifier | `decorator` |
| JSX tag identifier | `tag` |
| JSX attribute name | `attribute` |

Consequences are intentional:

- A reference to a parameter is `variable`, not `parameter`.
- A reference to an interface is `type`, not `interface`.
- A reference to a type parameter is `type`, not `type-parameter`.
- A bare reference to a function value is `variable`; the same identifier used as `fn()` is `function`.
- A bare reference to a class value is `variable`; the same identifier used as `new Foo()` is `class`, and in a type annotation it is `type`.
- An enum member used through member access is locally a `property`; its declaration remains `enum-member`.

## Boundary semantics

This contract does not change lexical-span boundaries.

Strings, comments, regular expressions, operators, punctuation, JSX text handling, JSX fragment punctuation, and template-literal segmentation keep their existing boundary rules. Template-literal text remains `string`; `${...}` returns to JavaScript/TypeScript semantics.

## Layer boundary

Semantic highlighting answers:

> What role does this span play here?

A future symbol-intelligence layer may answer:

> Which declaration does this reference resolve to?

That future layer may provide symbol identity, declaration location, find-references, rename, cross-file resolution, and project-level relationships. Those capabilities are not required by this highlighting contract.
