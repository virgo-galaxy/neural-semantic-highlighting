# Independent HTML Golden

`golden.json` uses independently authored `⟦role+modifier|source⟧` expectations.
Remove markers before labeling; compute UTF-16 offsets from original marked
source, never regenerate expected roles from parser output. Embedded-role markers
also independently identify expected raw body regions.

Coverage includes modern/custom elements, declarative shadow DOM, SVG/MathML,
CDATA, optional end tags, boolean/quoted/unquoted attributes, Tailwind strings,
entities, astral Unicode/CRLF, RCDATA and distinct script/style/data blocks.
Fixtures and Playground demonstration sources must not enter training corpora.
