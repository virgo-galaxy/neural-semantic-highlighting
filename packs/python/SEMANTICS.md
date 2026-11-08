# Python semantic contract

Modern Python 3 original source, including functions/classes, imports, annotations,
decorators, async/await, generators, comprehensions, pattern matching and generic
type parameters. File suffixes `.py`, `.pyw`, `.pyi` share the `python` document kind.
Offline parsing uses a separately pinned modern CPython; neural inference remains
on the existing PyTorch environment and does not import an AST/tokenizer.

## Local roles

| Source                                     | Role / modifiers                                                                                    |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| Keywords and syntactic soft keywords       | `keyword`; contextual `match`, `case`, `type` are not globally reserved identifiers                 |
| Comments and shebangs                      | `comment`, including `#`                                                                            |
| Strings, bytes, docstrings, f/t-strings    | `string`, complete original prefix/delimiters/interpolation; adjacent source literals stay separate |
| Numeric literals                           | `number`                                                                                            |
| Operators                                  | `operator`, including assignment, walrus, arrows, unpacking and arithmetic                          |
| Delimiters                                 | `punctuation`: parentheses, braces, brackets, comma, colon, dot, semicolon, decorator `@`           |
| Imported module components / aliases       | `namespace`; imported objects remain local names without fetching modules                           |
| Annotation identifiers and type parameters | `type`; declarations have `declaration`                                                             |
| Class name                                 | `class`; declaration has `declaration`                                                              |
| Function/method name                       | `function` / `method`; declaration has `declaration`, with `async`/`generator` when applicable      |
| Function/lambda argument                   | `parameter`; declaration has `declaration`                                                          |
| Assignment/loop/with/match bindings        | `variable`; declaration has `declaration`                                                           |
| Attribute member                           | `method` at call sites, otherwise `property`; no cross-file type resolution                         |
| Decorator callable name                    | `decorator`; arguments retain ordinary code roles                                                   |
| Recognized unshadowed builtins             | Relevant local role plus `default-library`                                                          |

Name references use lexical scope where available. A direct unknown callable is
`function`; an ordinary unresolved name is `variable`. The teacher describes
source-local syntax/roles, not complete Python name resolution or framework APIs.
No imported source, user object, decorator or annotation is evaluated.

Formatted and template strings deliberately remain whole string spans in this
first contract. Their interpolation expressions are not separately composed.
This retains quoted/raw/triple-quoted content and avoids claiming expression-level
semantics inside a string. Long strings/comments beyond 512 bytes remain measured
neural limitations, not a promise of parser-equivalent recognition.

## Invariants and evaluation

- Sorted nonempty nonoverlapping UTF-16 `[start,end)` spans, aligned to complete
  Unicode characters. Original source, line endings and spelling remain intact.
- Every non-whitespace Gold character has a role. Explicit line-continuation
  backslashes are punctuation. Parse/token/range failures are quarantined, never
  completed with guessed roles or executed to discover semantics.
- Offline AST byte columns and tokenizer character columns are converted through
  original-source coordinates. Unicode before a token must not shift its range.
- Golden and Playground examples are outside collection roots. Source directories
  and related copies are grouped before windows, with separate natural/focus
  reporting and frozen family assignments across experiments.
- Training validation never uses Gold cursor cuts. Runtime/adaptive evaluation
  uses predicted boundaries only. Independent test is reserved for one reviewed
  frozen candidate, with per-role/features and explicit coverage gaps.
- This is a code-display engine. Python 2, notebooks as JSON containers, console
  transcripts, embedded foreign DSL parsing, execution, type checking and import
  resolution are separate scopes.
