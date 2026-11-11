# Known issues

The initial CSS-family model is usable for ordinary declarations, common
selectors, custom properties, functions, Sass modules/mixins and Less mixins.
Its predictions are imperfect; the following limits were observed in independent
Golden development probes or are explicit coverage gaps.

- **Complex selectors:** chained pseudo classes/elements and ID selectors can
  acquire string/attribute roles or split boundaries. The `button.primary:not(...)`
  probe still fails. Type selectors also score lower than common declarations.
- **Raw URLs and comments:** unquoted `url(https://...)` near a Sass line comment
  can merge with the function or consume following code as string/comment. Long
  strings and comments crossing the 512-byte context remain risky. Runtime has
  no parser or lexical repair pass.
- **Interpolation and parameter roles:** Less `@{name}` and Sass `#{...}` can
  have incorrect spans; a variable reference may be labeled parameter. Quoted
  interpolation deliberately remains a whole string in this semantic contract.
- **Sparse modern values:** in the reviewed Surface layout, `auto-fit` is a
  variable rather than a keyword; all other spans and declaration modifiers match.
  Adding Pico covers this spelling in training but did not eliminate the probe's
  error. No runtime spelling override is applied.
- **CRLF and Unicode coverage:** the corpus has no CRLF training documents.
  Original characters and UTF-16 offsets remain preserved, but `\r` may receive
  its own predicted span or join a comment. Astral characters in a comment can
  therefore fail exact-span matching without splitting the Unicode character.
- **Rare-role evidence:** CSS test has just five documents and six comments.
  SCSS test has no Gold parameter declarations or ID labels; its parameter
  support in validation is two. Less test has only four parameter declarations.
  A good aggregate score does not establish these roles across arbitrary code.
- **Offline parser coverage:** the pinned Gold parser quarantines Pico
  `forms/_input-date.scss` and Ant Design Less `progress/style/index-pure.less`,
  `skeleton/style/index-pure.less`, `skeleton/style/rtl.less`. These source files
  remain preserved; exclusion is not a claim that their syntax is invalid.
- **Scope and runtime:** `.sass` indentation, Stylus and embedded Vue/HTML style
  sections are outside this pack. Imports are not resolved and preprocessors are
  not executed. HTML/Vue/Svelte composition can reuse this pack for predicted style
  regions. Playground and frontend inference use the selected ONNX model in the
  browser Worker without a Python bridge. [Browser verification](../../../docs/browser-runtime.md)
  establishes execution consistency, without resolving the prediction limits above.

See the raw per-kind/per-role reports and the visible probe mismatches. Further
work should start from product code failures and a short measured experiment,
while preserving this baseline, rather than repeatedly optimizing the test score
or treating every edge case as a reason for indefinite training.
