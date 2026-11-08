# Vue semantic contract

Original `.vue` SFC source, with shared markup roles and original UTF-16 `[start,end)`
offsets. Vue 2 and Vue 3 syntax are both intentional targets. Vue 3.2 is a Vue 3
coverage profile, not a separate language or a reason to retrain JS/TS/styles.
This is source highlighting, not compilation, execution or version validation.

## Coverage profiles

- Vue 2: Options API, filters, `slot`/`slot-scope`, `v-slot`, `.sync`, `.native`,
  custom directives and dynamic arguments. Vue 2.6/2.7 remain deliberate coverage
  despite APIs being removed from Vue 3.
- Vue 3: Options API, `setup()`, fragments, named/scoped slots, `v-model` arguments
  and modifiers, Teleport, Suspense and ordinary template directives.
- Vue 3.2: JS/TS `script setup`, `defineProps`, `defineEmits`, `defineExpose`,
  `withDefaults`, coexisting normal/setup scripts and scoped CSS `v-bind()`.
  Later compiler macros remain ordinary source identifiers; no compiler-version
  compatibility is inferred from lexical highlighting.

Primary references: [Vue migration](https://v3-migration.vuejs.org/breaking-changes/),
[filters](https://v3-migration.vuejs.org/breaking-changes/filters.html),
[v-model](https://v3-migration.vuejs.org/breaking-changes/v-model.html),
[script setup](https://vuejs.org/api/sfc-script-setup).

## Roles and composition

Tag names, delimiters, comments, text and entities follow the HTML pack's role
conventions. End-tag names have `closing`. Do not synthesize implied tags or
change original case, whitespace, entities, Unicode or CRLF.

Every whole attribute name is `attribute`, including `v-if`, `v-for`, `:prop`,
`@[event].stop`, `#[slot]` and custom directive modifiers. Each equals sign is
`punctuation`; a complete quoted/unquoted value is `string`. This first Vue
contract deliberately keeps directive value expressions, dynamic argument code,
slot destructuring, inline style/event snippets and Tailwind classes within those
whole attribute spans. It does not claim expression-level semantic roles there.

Interpolation `{{` and `}}` are separate `punctuation` spans; the original interior
is one `embedded-expression` region. Composition wraps that source in a fixed
expression context for the existing TypeScript neural model, then projects only
the original interior back to its UTF-16 coordinates. Vue 2 filter pipes receive
ordinary operator/identifier/call roles, not compiler-specific filter resolution.
Encoded entity expressions require separately verified mapping; unsupported
composed reference syntax is explicitly counted, never silently fabricated.

Script bodies use `embedded-javascript`, `embedded-typescript`, `embedded-jsx` or
`embedded-tsx`, according to offline source-language declarations. Style bodies
use `embedded-css`, `embedded-scss` or `embedded-less`; `scoped`, `module`, ordering
and a normal/setup script pair do not change the underlying child language.
Custom blocks and unsupported preprocessors (`pug`, indentation Sass, Stylus)
remain opaque `embedded-data`. External `src` and imports never fetch anything.
Nested template `script`/`style` raw bodies follow their declared syntax too.

The compact model schema contains only markup and region roles. The public schema
adds existing child-model roles/modifiers. Base recognition and actual composed
semantics are distinct evaluation scopes, with version/feature breakdowns and
explicit unsupported-Gold counts. Existing child-model limitations still apply.

## Runtime invariants

All region selection comes from the Vue neural model. No runtime Vue/HTML parser,
regex language detector, Gold cuts or source-spelling repair may choose a region.
Composition reuses the existing `SemanticPack` contract and lazy local processes;
input code is never executed. Sorted nonoverlapping spans must align to whole
Unicode characters. Source-preserving rendering is distinct from role accuracy.

Offline Vue parsing may recognize both version dialects without compiling them.
Incomplete coverage and malformed syntax are quarantined with original bytes and
reasons. Training and evaluation use frozen source, separate natural/focus streams
and intact directory/template groups before windows. Golden/Playground examples
are never collected. Real validation and visible failures guide bounded runs;
final test remains reserved for a frozen reviewed candidate.
