# Known issues

This is a usable initial SFC baseline with versioned coverage, not a claim that
every Vue compiler feature or source shape is perfect.

- **Scope of template expressions:** directive names/arguments/modifiers are whole
  attributes, and quoted/unquoted values stay whole strings. `v-for` bindings,
  event statements, slot destructuring and dynamic-argument code do not yet get
  expression-level child semantics. Mustache interiors do. Vue 2 filter pipes use
  ordinary operator/identifier/call roles, without framework filter resolution.
- **Dual-script TSX and raw boundaries:** the independent adjacent normal/setup
  TSX probe still fragments JSX content as markup. Ordinary TSX-render and typed
  setup demonstrations work substantially better, but do not establish all such
  combinations. Less module/custom-block boundaries can include the preceding
  `>` or split near a brace. These mismatches remain in the Golden report.
- **Language-role confusion:** JavaScript bodies can be predicted as TypeScript,
  and body/type changes can fragment one block. Both script kinds reuse the same
  model, but independent fragment inference loses context. Source beyond the
  512-byte window has no recurrent document state. Raw strings, comments, entities
  and template-like text can still cross modes incorrectly.
- **Opaque syntax:** Pug, indentation Sass, Stylus and custom-block languages have
  no dedicated model. Gold marks them opaque data, but the visible Pug case still
  receives text roles. No runtime parser or spelling repair conceals this error.
  Encoded entities in executable expressions and unusual Vue 2 filters require
  separately verified mapping/reference coverage; ordinary attribute strings
  preserve entities unchanged. Tailwind values remain complete strings.
- **Sparse real evidence:** natural test is five Vue 2 components, four Vue 3 and
  one Vue 3.2. That last component has only 65 composed spans. Natural test contains
  no embedded style/JSX/TSX/data bodies; validation has only one short CSS body.
  Focus/Golden and development examples cover more syntax but are not substitutes
  for a larger independent real-source corpus. Read per-profile/per-role counts.
- **Inherited child limits:** existing JS/TS RegExp, comments, long strings and
  CSS-family selector/URL/interpolation limitations also apply here. CSS `v-bind`,
  scoped/deep selectors and render code are highlighted lexically; framework
  macros, imports, component identities and CSS Modules are not resolved/executed.
- **Runtime:** one Vue entry covers all profiles through the local Vite/Python
  bridge. No browser-native inference or framework compiler is bundled.

Original source and Unicode alignment are preserved even when roles are wrong.
Further work should start from a product failure and a short measured experiment,
keeping this baseline and the fixed holdouts intact. Do not indefinitely retrain
or repeatedly tune against the final test.
