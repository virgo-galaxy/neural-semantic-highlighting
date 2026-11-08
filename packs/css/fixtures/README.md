# CSS / SCSS / Less Golden fixtures

`golden.json` contains independently written, complete expected spans. Each
`⟦type+modifier|text⟧` marker describes an exact source span. Tests remove the
markers before passing source to the offline labeler. Offsets come only from
the marked source, never from the labeler's output.

Cases cover CSS, SCSS and Less independently, selectors, custom properties, queries,
functions, module calls, declaration modifiers, raw URLs versus line comments,
interpolation policy, astral Unicode, escapes and original CRLF line endings.
Fixtures and challenge material must never enter training data.
