# Known issues

The initial modern HTML model handles ordinary tags, attributes, optional ends,
custom elements and common embedded bodies. Its failures are visible and retained:

- **Raw-text context:** JS strings containing `<tag>` may be classified as markup.
  RCDATA in `textarea` and foreign CDATA can acquire tag, comment or entity roles.
  JSON/import-map data can split at its last brace or be partly mistaken for code.
  These are modern supported source contexts, with imperfect neural predictions.
- **Exact boundaries:** unquoted `type=email required` can merge into one value;
  `<br/>` may merge its name and delimiter. Comments can include a trailing CR or
  split near their closing delimiter. Text whitespace, short MathML text, and
  inline attribute-value endings can get wrong boundaries or roles.
- **Embedded-region leakage:** long CSS attribute selectors and code strings may
  split a body into fragments, and plain text can acquire an embedded role. The
  composite faithfully uses predicted regions, so a wrong region can produce
  extra child-language spans. High character coverage hides these exact errors.
  The 512-byte window has no recurrent document state; long raw contexts remain
  a limitation. No parser or source spelling repair conceals these failures.
- **Child model limits:** existing JS regular-expression/comment/long-string and
  CSS selector/URL/interpolation limitations also apply after composition. Child
  Gold cannot completely cover two real held-out documents; they are explicitly
  excluded only from composed reference scoring. See raw reports for identities.
- **Sparse evidence:** real test has ten base documents, three JS bodies, two CSS
  bodies, one data body, two entities and no HTML comments. Validation has only
  two comments and no entities/data. Golden probes and synthetic family holdouts
  expose failures, but do not replace a larger independent real-source evaluation.
- **Deliberate scope:** Tailwind class values and `style`/event attributes remain
  whole strings; attributes do not invoke child packs. `.vue`, Svelte, server
  templates, JSX and TSX are separate kinds. Explicitly obsolete HTML is not a
  target. Imports/resources are never resolved and source is never executed.
- **Runtime:** Playground and frontend consumers use the selected ONNX model in
  the browser Worker. HTML composition loads existing JS/TS/CSS models for predicted
  embedded regions, without Python or a source parser. [Browser verification](../../../docs/browser-runtime.md)
  establishes consistent execution, not improved model accuracy.

Source characters and UTF-16 alignment remain intact even when roles are wrong.
Use this as a documented initial baseline. Further work should start from actual
product failures, with a short measured experiment, rather than indefinite runs
or repeated optimization against this test split.
