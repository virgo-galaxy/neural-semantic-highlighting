# HTML semantic contract

The `html` document kind covers original modern HTML documents and fragments.
Use the current [WHATWG HTML Living Standard](https://html.spec.whatwg.org/),
including less common conforming elements, custom elements, templates/slots,
declarative shadow DOM, SVG and MathML. This is source highlighting, not DOM
execution, a conformance checker, resource fetching or template compilation.

## Source roles

| Source                                      | Role                  | Boundaries / modifiers                                                   |
| ------------------------------------------- | --------------------- | ------------------------------------------------------------------------ |
| Modern HTML doctype                         | `keyword`             | Entire original declaration                                              |
| Comment                                     | `comment`             | Includes original delimiters                                             |
| Start/end tag name                          | `tag`                 | Name only; end-tag names have `closing`                                  |
| Tag delimiters and attribute equals         | `punctuation`         | `<`, `</`, `>`, `/>`, `=` individually                                   |
| Attribute name                              | `attribute`           | Original spelling, including `data-*`, `aria-*`, qualified foreign names |
| Attribute value                             | `string`              | Includes quotes when present; unquoted values retain original boundaries |
| Ordinary content                            | `text`                | Contiguous source text, not a symbol role                                |
| Character reference in ordinary/RCDATA text | `entity`              | Original reference spelling, never decoded source                        |
| JavaScript script body                      | `embedded-javascript` | Body only; entire raw region, including internal whitespace              |
| CSS style body                              | `embedded-css`        | Body only; entire raw region, including internal whitespace              |
| Other script/style data body                | `embedded-data`       | Body only; no false JavaScript/CSS claim                                 |

Whitespace between markup tokens is outside spans. Attribute values, comments,
text and embedded bodies preserve their own internal whitespace. Closing-tag
punctuation is distinct from the tag name. HTML optional end tags are permitted;
an absent source tag must never produce a synthetic span.

`class` values, including Tailwind classes/variants/arbitrary values, remain whole
attribute strings. Tailwind is not a separate document kind. `style` and event
attributes also remain strings in the first contract; their code-fragment
interpretation requires a separately measured capability. Quoted character
references remain inside the attribute string.

Offline Gold marks script types and body regions. Omitted/empty JavaScript types
and `module` identify JavaScript; JSON, import maps and unknown types stay data.
An external `src` never causes a fetch. Style bodies are CSS unless their type
declares another syntax. Region recognition is distinct from the accuracy of the
JS/CSS predictions eventually composed into those regions.

## Runtime and invariants

- UTF-16 `[start,end)` offsets, sorted, nonempty, nonoverlapping spans aligned
  to whole Unicode characters. Original bytes, entities, CRLF and case survive.
- Every non-whitespace Gold source character has a role. Gaps or malformed
  lexical material fail explicitly rather than receiving invented valid Gold.
- Parsers and entity decoders are offline Gold tools only. Runtime uses neural
  predictions. Composed JS/CSS inference must use predicted regions, never Gold
  cuts, runtime parsers or regular-expression language detection.
- Plain HTML, embedded-body region recognition, composed JS/CSS, and attribute
  fragments are separate evaluation scopes. A base-model score does not prove
  complete mixed-language highlighting.
- Server-template dialects and Vue/Svelte component syntax are separate scopes;
  do not infer their support from the `.html` extension.

## Modern coverage

Training sources should not target explicitly obsolete HTML elements or legacy
doctypes/presentational features. Offline exclusion reasons remain auditable.
Do not equate old-looking but conforming elements such as `b`, `i`, `small`, `ruby`
or uncommon current elements with obsolete syntax. Gold is vocabulary-agnostic
for conforming/custom/foreign tag names; no small popular-tag allowlist limits
the lexical roles. Robust source rendering is independent of conformance.
