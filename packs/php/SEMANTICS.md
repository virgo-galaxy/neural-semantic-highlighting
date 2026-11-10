# PHP semantic contract

One `php` kind covers original `.php` / `.phtml` source, conventional `<?php` and
`<?=` tags, tagless PHP snippets and bounded PHP/HTML templates. Target common
modern PHP 8 forms: functions, classes/interfaces/traits/enums, typed/promoted
parameters, properties, attributes, named arguments, arrays/destructuring, closures
and arrow functions, match/nullsafe/coalescing syntax, exceptions and generators.
It does not certify every newest language feature, framework DSL or PHP extension.

No PHP interpreter, SDK, Composer, web server or project environment is installed.
Gold builds pinned Tree-sitter 0.25.10 / PHP grammar 0.24.1 using the existing
native compiler in project cache. It parses original source without loading,
including or executing PHP code, autoloaders, dependencies or applications.

| Source                                                                                                 | Base role                                                            |
| ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| Language/type words, PHP open/close tags and magic language constants                                  | `keyword`                                                            |
| Original line/block/DocBlock comments                                                                  | `comment`                                                            |
| Single/double quoted literal pieces, escapes, heredoc/nowdoc markers and content                       | `string`                                                             |
| Numeric literals                                                                                       | `number`                                                             |
| Assignment/arithmetic/comparison, concatenation, array arrow and member/scope operators                | `operator`                                                           |
| Brackets/braces/parentheses, commas/semicolons, namespace separators, attribute opener and initial BOM | `punctuation`                                                        |
| Namespace segments                                                                                     | `namespace`                                                          |
| Named type positions                                                                                   | `type`, preserving locally known class/interface/trait/enum          |
| Class/interface/trait/enum declarations and references                                                 | `class` / `interface` / `trait` / `enum`                             |
| Enum cases                                                                                             | `enum-member`                                                        |
| Function/method names and calls                                                                        | `function`; `__construct`/`__destruct` definitions use `constructor` |
| Formal/promoted parameters and visible references                                                      | `parameter`                                                          |
| Whole `$variable` names, implicit assignments, foreach/catch/destructuring names                       | `variable`                                                           |
| Property declarations/access                                                                           | `property`                                                           |
| Constants / class constants                                                                            | `constant`                                                           |
| Labels / goto targets                                                                                  | `label`                                                              |
| Attribute names                                                                                        | `decorator`                                                          |
| Original text outside PHP tags                                                                         | `embedded-html`, complete original region                            |

A `$variable` is one original token, including `$`. First local assignment carries
`declaration`; reassigning a known binding preserves its role without declaring it
again. Formal/property/import/type/function definitions also carry `declaration`.
DocBlock syntax is comment text, not separately resolved generic/project types.
Promoted parameters use `parameter` at the definition and `property` at member access.

Interpolated variables/access expressions inside double quotes and heredocs remain
visible PHP roles. Literal fragments and original delimiters use `string`; nowdoc
contents remain opaque, including `$`. Touching string/comment/HTML spans coalesce
according to the same pack decoder policy in Gold and inference. Whitespace gaps
between distinct syntax tokens remain gaps, never normalized or invented source.

The offline grammar chooses PHP-only parsing for tagless code, and PHP+HTML parsing
for sources starting with markup/tags. Invalid tagless PHP cannot fall back to an
opaque valid HTML document. Runtime never chooses or runs a parser. Optional short
`<?` opening tags, Blade/Twig/framework templates and non-PHP file formats are not
claimed. Unsupported syntax or invalid/uncovered source is quarantined.

## HTML composition and evidence

The base PHP model learns PHP roles and `embedded-html` region boundaries.
The public composite delegates **only predicted HTML regions** to the existing
HTML model, which can reuse existing JS/CSS models. No source tag scanning, runtime
parsing, PHP execution or Gold region cuts are used. Child tokens retain their
own `documentKind` and language vocabulary. PHP's schema describes the base model;
composed child roles belong to their existing child models.

PHP syntax/region F1 and composed template quality are separate evidence. A base
score alone cannot establish whole-template accuracy. Fragmented tags/attributes,
PHP inside HTML/JS/CSS strings, long regions and wrong predicted cuts can reduce
composition quality. Original entities and HTML content are never decoded/rewritten.

## Invariants and workflow

- Sorted, nonempty, nonoverlapping UTF-16 `[start,end)` spans cover every original
  non-whitespace character. Preserve BOM, CRLF, Unicode, astral characters, quotes,
  escapes and layout. Never execute source to obtain labels or inference.
- Original bytes, complete licenses, upstream Git blobs, parser/compiler/library
  hashes and quarantines remain external under `~/Datasets/neural-semantic-highlighting/php`.
- Exact/lexical/normalized copies are audited before source/task family allocation.
  Freeze assignments before training and retain all old assignments for revisions.
  Golden and Playground are excluded. Natural/focus/visible evidence stay separate.
- Keep the existing four-layer, 512-byte architecture. Start with smoke and a short
  measured experiment, inspect real validation source and Golden, then freeze before
  first test. Never tune after first test inspection for the same held-out protocol.
- Full optimizer/RNG checkpoints stay in `artifacts/php`. Resume the original
  `last.pt`; fresh transfer uses only compatible complete training checkpoints.
  Never initialize/resume from selected inference `.pt` or browser ONNX exports.
- Preserve all existing models, datasets and experiments. Browser inference needs
  no Python/PHP provider, SDK, server, parser, Composer or installed dependencies.
