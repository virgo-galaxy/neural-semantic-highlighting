# Python measured limits

This is the reviewed epoch-7 fragment candidate. Remaining errors are retained as
development evidence; no regex/parser repair participates in runtime inference.

- **Name roles need context.** Natural test namespace/type/class/function F1 is
  0.6835/0.5810/0.5000/0.5968; parameter/variable F1 is 0.7173/0.6716. In real
  validation, parameter references beyond their declaration window often become
  variables, and imported or unresolved names may get another source-local role.
  The teacher itself does not perform cross-file type/import resolution. Many
  parameter/variable and type/class confusions share current theme colors, but
  consumers relying on exact roles must account for these errors.
- **Long strings and docstrings can fragment.** Natural test string F1 is 0.7754.
  Real validation includes triple-quoted docstrings split into several string
  spans, sometimes with incorrectly styled interior tokens. A 512-byte cursor
  does not retain complete lexical state across arbitrarily long text. There is
  no claim that increasing rounds alone solves this.
- **Short fragments are improved, not exact.** The Golden import alias `as` can
  become namespace; a decorator callable can become method; a wildcard-match
  `pass` can become variable. Builtin shadowing can be missed, e.g. a parameter
  named `len` used as a callable. These are explicit failures in the raw probes.
- **Whitespace edges remain imperfect.** A CRLF comment may include the CR in its
  predicted span. An f-string immediately followed by another string may include
  the separating space. These are exact-span errors even when styling appears
  continuous. No trimming or coalescing rule hides them.
- **Modifiers are less reliable than common syntax.** Golden functions can receive
  an extra `generator`, and call-site names/keyword arguments can receive
  `declaration`. Complete-string f/t-string interpolation is deliberate scope;
  inner expressions have no separate child model. Rare modern features with no
  held-out evidence must not be advertised as verified by the compiler version.

Next improvements should begin with real product snippets and broader independent
natural coverage, preserving family holdouts. The four natural test documents
provide limited evidence; do not repeatedly optimize against them. Existing
checkpoints, data revisions and formal models remain preserved.
