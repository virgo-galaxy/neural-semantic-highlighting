# Svelte semantic contract

Original `.svelte` components, UTF-16 half-open coordinates. Cover legacy Svelte
3/4 component syntax and modern Svelte 5 syntax accepted by the pinned offline
5.38.0 parser. This is highlighting, not compiler compatibility validation.

Markup uses `tag`, `attribute`, `string`, `text`, `entity`, `comment` and
`punctuation`. Closing tag names have `closing`. Preserve original spelling,
Unicode, whitespace, BOM and CRLF; never synthesize implied HTML tags.

Whole directive/shorthand/spread attributes are `attribute`; ordinary attribute
names are `attribute`, equals signs `punctuation`, complete values `string`.
This first baseline deliberately keeps event handlers, bind/class/style/use/on
directives, quoted interpolations, Tailwind classes and spreads opaque inside
attribute spans, like the existing Vue contract. It does not claim semantic roles
inside those attribute expressions.

Template interpolation braces are punctuation; the compiler's original expression
range is `embedded-expression`. Block markers (`#if`, `:else`, `/each`, `@render`,
etc.) are `keyword`; header delimiters are punctuation, remaining binding names
are `variable`, digits `number`, other symbols `operator`. If/each/await/key
expressions and render/html expressions are separate embedded regions. Snippet
names/parameters and await/each bindings receive local lexical roles; this model
does not resolve their references or component symbols across files.

Script bodies are `embedded-javascript` or `embedded-typescript`; style bodies
`embedded-css`, `embedded-scss` or `embedded-less`. Unsupported languages are
opaque `embedded-data`. Module/instance scripts, runes, legacy exports/reactive
statements and style ordering reuse existing JS/TS and style models.

The offline teacher uses the official compiler only for parse/preprocess. Its
style callback masks each original UTF-16 unit with a space, preserving newlines
and length, so SCSS/Less never require a preprocessor installation. The original
style bytes are always the labeled region. No component, import, event handler,
project config or external preprocessor is executed or fetched by labeling.
Malformed syntax and incomplete coverage are quarantined, never relabeled by
guessed fallback syntax. Unknown compiler nodes fail closed.

At runtime only the neural model selects regions. Composition passes those
regions to existing JS/TS/CSS models. Expressions use a fixed TS expression
wrapper and are clipped back to original coordinates. No compiler, AST, regex
language detector, Gold cuts or source-spelling repair selects a runtime region.
Base template/region scores and composed visible-code evidence are distinct.
Inherited JS/TS/CSS limitations apply. Natural and focused streams keep immutable
source-family splits before windows; Golden/Playground are never training input.
