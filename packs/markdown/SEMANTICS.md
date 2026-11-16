# Markdown source-local semantic contract

One `markdown` kind/profile covers `.md`, `.markdown`, `.mdown` and `.mkd` source.
Aliases are explicit frontend language IDs. This baseline covers common Markdown
and measured GFM tables, task lists, strikethrough and autolinks. MDX, document
rendering, template engines, mathematics and every extension are separate scopes.
See [GFM](https://github.github.com/gfm/) and
[Prettier's Markdown parser](https://github.com/prettier/prettier/tree/main/src/language-markdown).

Offline supervision uses the existing pinned Prettier 3.9.6 Markdown/remark parser
through its parse-only API. No formatting, Markdown-to-HTML rendering, source/code
execution, new dependency or language SDK installation occurs. Original parser,
entity decoder and Node assets are fingerprinted. The parser normalizes BOM and
line endings internally: a checked UTF-16 boundary map returns every AST position
to the original source, preserving BOM, CRLF, bare CR and astral characters.
Unexpected preprocessing, unknown AST nodes, uncovered material or overlapping
ranges fail closed and quarantine the unchanged source.

| Source                                              | Role / modifiers                                              | Original boundaries                                         |
| --------------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------- |
| Paragraph / ordinary prose                          | `text`                                                        | Original parser text run; whitespace-only gaps omitted      |
| ATX / setext heading content and table headers      | `heading`                                                     | Content, keeping inline children separate                   |
| Heading/list/quote/rule/table/link/emphasis markers | `punctuation`                                                 | Original delimiter runs; exterior whitespace omitted        |
| Bold, italic, deletion content                      | Existing content role + `strong`, `emphasis`, `strikethrough` | Nested modifiers accumulate; markers remain separate        |
| Task checkbox                                       | `keyword`                                                     | Original `[ ]`, `[x]` or `[X]`                              |
| Inline code / indented or container code            | `code`                                                        | Opaque original region, including inline backticks          |
| Link/image caption / reference identifier           | `link`                                                        | Original text, retaining inline children when available     |
| Link destination / full-reference target            | `link-destination`                                            | Original destination, including angle brackets when present |
| Link title / fence metadata                         | `string`                                                      | Original quoted title or opaque metadata content            |
| Valid character reference / escaped marker          | `entity`                                                      | Original spelling, never decoded source                     |
| HTML comment                                        | `comment`                                                     | Whole original delimiters                                   |
| Other raw HTML                                      | `string`                                                      | Opaque source; never inserted as executable HTML            |
| YAML/TOML-style front matter accepted by parser     | `code`                                                        | Opaque original block; no configuration evaluation          |
| Top-level opening/closing fenced-code delimiter     | `code-fence`                                                  | Original backticks/tilde run                                |
| First explicit fence info word                      | `code-language`                                               | Original word; additional metadata remains opaque           |
| Top-level fenced body                               | `embedded-code`                                               | Whole contiguous original body, including its line breaks   |

Gold covers every non-whitespace source character with sorted nonempty,
nonoverlapping UTF-16 ranges. Unclosed fences consume existing source only; empty
fences never invent a body. Nested/list/quote and indented code remain opaque
rather than stripping container prefixes or reconstructing synthetic source.
References are highlighted as source; images, links, HTML and metadata never load
resources or execute. Unsupported syntax may remain ordinary Markdown text; an
accepted document is not a guarantee of every dialect or extension.

Runtime uses only neural predictions. Composition pairs predicted `code-fence`,
`code-language` and `embedded-code` spans. It reads the explicit info word from
that predicted span, normalizes registered language aliases, and invokes the
already registered child model on the predicted original body. It never scans
source fences, applies source regexes, parses Markdown, inspects code content to
guess a language, or uses Gold boundaries. Missing/unknown/unregistered/Markdown
info words leave the body as `code`; recursive Markdown composition is disabled.
Invalid child/base offsets fail. Returned child spans retain document kinds and
original offsets. The default highlighter registers existing languages; a
selective Markdown import bundles only Markdown until child descriptors are
explicitly registered. No Python process or offline parser enters the frontend.

Base Markdown quality, predicted fence routing, child-model quality and exact
browser/native parity are separate evidence. A base score does not establish
complete composed code accuracy. Context remains 512 original UTF-8 bytes;
long prose/URLs/code bodies, nested modifiers and region boundaries are measured
limits. Preserve every dataset revision, checkpoint and old formal model. Resume
full optimizer/RNG checkpoints under artifacts only, never inference .pt/ONNX.
