# CSS family semantic contract

CSS and SCSS label the local role of each original source span. This is source
highlighting, not Sass execution, selector matching, CSS validation, or project
symbol resolution. Document kinds are `css` and `scss`; one model learns both.

## Roles

| Source role                                                     | Type          | Boundary / modifiers                                    |
| --------------------------------------------------------------- | ------------- | ------------------------------------------------------- |
| Type selector, e.g. `button`                                    | `tag`         | Identifier                                              |
| Class selector, e.g. `.root`                                    | `class`       | Includes `.`                                            |
| Sass placeholder, e.g. `%shared`                                | `class`       | Includes `%`                                            |
| ID selector, e.g. `#main`                                       | `label`       | Includes `#`                                            |
| Pseudo-class/element, e.g. `:hover`, `::before`                 | `function`    | Includes colons; excludes arguments                     |
| Attribute selector name                                         | `attribute`   | Name only; brackets/operators/values stay separate      |
| Declaration property, including `--custom`                      | `property`    | `declaration` modifier                                  |
| Value identifier, e.g. `grid`, `auto-fit`, `red`                | `keyword`     | Identifier; not a property declaration                  |
| At-keyword, e.g. `@media`, `@mixin`                             | `keyword`     | Includes `@`                                            |
| Number, dimension or percentage                                 | `number`      | Includes sign and unit when one lexical token           |
| Hex color                                                       | `number`      | Whole literal, e.g. `#aabbcc`                           |
| Function/mixin declaration name                                 | `function`    | Name only; `declaration` modifier                       |
| Function/mixin call name                                        | `function`    | Name only; excludes parentheses                         |
| Sass function/mixin parameter declaration                       | `parameter`   | Includes `$`; `declaration` modifier                    |
| Sass variable declaration                                       | `variable`    | Includes `$`; `declaration` modifier                    |
| Sass variable reference                                         | `variable`    | Includes `$`; references retain local value role        |
| CSS custom-property reference                                   | `variable`    | Whole `--name` in `var()`                               |
| Sass module qualifier                                           | `namespace`   | Qualifier identifier, not the member name               |
| Comment                                                         | `comment`     | Whole comment, including delimiters                     |
| Quoted string                                                   | `string`      | Includes quotes and escapes                             |
| URL payload                                                     | `string`      | Content inside `url()`; excludes surrounding whitespace |
| Combinator, arithmetic/comparison operator, parent selector `&` | `operator`    | Lexical operator                                        |
| Braces, brackets, parentheses, commas, colons and semicolons    | `punctuation` | Individual lexical token                                |

Sass interpolation outside quoted strings returns to expression roles; `#{` and
`}` are punctuation. In the initial contract a quoted Sass string, including its
interpolated contents, remains one `string` span. Splitting string interpolation
into expression subspans would require an explicit contract/data/model revision.
No hidden interpolation claim should be inferred from the `scss` manifest entry.

## Invariants

- Offsets are UTF-16 code units with inclusive start and exclusive end.
- Spans are sorted, nonempty, nonoverlapping and aligned to complete Unicode code
  points. CRLF and original whitespace are preserved.
- All non-whitespace source characters receive Gold; strings and comments keep
  their internal whitespace. A parser failure or source gap must be reported,
  never converted into an apparently complete labeled document.
- Sass imports are not resolved and source programs are not compiled or executed.
  Undefined variables or unavailable imported mixins do not prevent local-role Gold.
- Modern syntax accepted by the pinned parser is eligible; unsupported syntax is
  quarantined with its source identity. Coverage counts must disclose exclusions.
- Runtime predictions come only from model weights and source bytes, using
  predicted adaptive cursor cuts and greedy decoding. Gold boundaries must never
  guide runtime inference.

## Golden evidence

Golden expectations are independently specified source/span/type/modifier cases,
not snapshots regenerated from the labeler during tests. Keep parsing validation,
Golden fixture correctness, training validation and held-out model test results
distinct. Collectors exclude repository fixtures and challenge material.
