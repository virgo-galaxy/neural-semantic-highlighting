# Markdown known issues

- Natural test exact-span F1 is 77.24%
  across 14 files; role macro F1 is
  71.03%. Bounded family holdouts limit
  generalization claims. Parser acceptance is not project/schema validity.
- This is an initial bounded Markdown baseline. On the natural holdout, embedded-code body exact-span F1 is 49.12% (19 reference bodies), heading F1 is 58.22% (180 spans), and prose text F1 is 60.52% (1304 spans); complete composed correctness is not established. Natural and visible evidence are base Markdown scores, not complete composed-code accuracy. Long wrapped prose, URL/title/reference boundaries, inline-code and raw-HTML/frontmatter boundaries remain approximate; strict Golden modifiers/boundaries are also weaker. Visible formatting.md is 78.16% F1, links.md 81.40%, and Unicode/frontmatter unicode.md 70.00%. The code.md Python body prediction omits its first import line, and an unknown-language body can be misclassified. Five of seven authored top-level code bodies have exact predicted body/info boundaries; TSX/JSON/CSS bodies in mixed.md and the XML body in unicode.md match. Composition runs on predicted regions only; it cannot fix missed/incorrect regions. Unknown/unregistered/recursive Markdown bodies remain code when their region is predicted. Nested/indented fences, front matter and raw HTML remain opaque; no MDX, math/template processing, Markdown document rendering, source execution or automatic language detection is claimed. Runtime performs no parser, regex or source-spelling repair.
- Prose/code/URL boundaries and nested formatting flags can have incorrect roles. Context is 512 original UTF-8 bytes; long/nested content and
  Unicode can split boundaries. No parser or spelling-based runtime fix hides these errors.
- The independent teacher passes 48 marked cases and 14
  tests; the neural model is entirely exact in 15/48
  Golden cases. Eight displays and 10 inspected natural validation files are
  development evidence, separate from the first held-out test. Original-text and
  browser parity checks establish consistency, not semantic perfection.
