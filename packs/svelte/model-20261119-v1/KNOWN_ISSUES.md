# Svelte known issues

A usable first template/composition baseline, with explicit limits:

- Natural held-out base template/region F1 is 88.47% over only
  9 files; role macro F1 is 58.49%.
  Rare header/binding/entity roles remain weaker than frequent markup. Do not
  replace this figure with the higher combined natural-plus-focus score.
- The eight visible composed components aggregate 97.53% exact-span F1.
  These are development probes, not an unseen composed test. Long bodies,
  template-looking text in JS comments/strings and boundaries next to markup can
  split, merge or receive the wrong language. Incorrect neural regions are never
  repaired by a runtime parser or tag scanner.
- Plain JS bodies can be predicted as TS. Most syntax shares the TS child model,
  but the child document-kind/theme accent can differ. CSS/SCSS/Less confusion,
  leading/trailing region boundaries and incomplete child fragments remain possible.
- Snippet parameter/name boundaries, keyed-each parentheses, await bindings,
  const/debug headers, nested control blocks, whitespace around text/entities and
  closing modifiers are imperfect. Only 8/20 neural Golden cases are completely
  exact; the separate offline teacher passes 20/20 independent marked cases.
- Directive/ordinary values (including event handlers and interpolated attribute
  strings) remain whole `string` spans; shorthand/spread attributes remain whole
  `attribute` spans. They do not receive inner JS semantic roles. Binding/header
  names use local lexical roles; component imports and cross-file symbols are not
  resolved. Complex typed/default/destructured snippet bindings are not certified.
- Legacy Svelte 3/4 syntax and common Svelte 5 syntax accepted by the pinned
  5.38.0 parser are targets. Newest compiler extensions, arbitrary malformed
  components, external preprocessors, indentation Sass, Stylus and custom
  template dialects are not certified. Unsupported style bodies are opaque.
- The unchanged 512-byte context limits distant declarations and region-language
  memory in very long bodies. Existing JS/TS and CSS model limitations also apply.
  Source preservation and exact browser/native parity do not mean perfect roles.

No Svelte app, compiler SDK, npm/global dependency or preprocessor was installed.
No component/import/config/handler is executed. The offline official parser is
cached in this project only; frontend inference depends on ONNX models alone.
Earlier datasets, experiments and all formal models remain preserved.
