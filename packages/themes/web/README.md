# Web themes

Theme definitions live here. They are build-time data; frontend consumers receive
CSS and need no theme compiler or JSON interpreter at runtime.

```text
src/
  schema.json
  base.css
  themes/
    default/
      theme.json
      light.json
      dark.json
      languages/
        typescript.json
        css.json
    muted/       # Same layout
    contrast/    # Same layout
scripts/build.mjs
dist/            # Generated; never edit by hand
```

`theme.json` supplies the stable ID, display name, description and optional order.
Every theme has complete `light.json` and `dark.json` palettes. Each palette
contains background, foreground, selection colors and all supported semantic
roles. Token styles are a six-digit hex color or an object with `color`, `bold`,
`italic`, `underline` and `strikethrough` properties.

Language files declare their `documentKinds`, with separate light/dark token
patches. Only differences are needed. TypeScript covers JS/TS modules,
declarations, JSX and TSX; CSS covers CSS/SCSS/Less. Other current languages use
the complete base palette until an actual visual need warrants a patch.

For each role, properties merge in order: the selected theme/mode's base style,
then that language's patch. Missing properties inherit; an explicit `false` clears
a boolean style. Missing language patches inherit this theme's base, not another
theme's colors. Unknown future token roles remain readable in the foreground color.

The build validates JSON Schema, rejects unknown roles, malformed colors and
conflicting family assignments, and produces low-specificity CSS. Every preset
writes a complete set of inherited palette variables, including language fallback
values, so switching presets cannot leave stale language colors behind.

```bash
pnpm --filter @nsh/themes build
```

The highlighter copies these outputs during its own build. `@nsh/themes` is a
build-only dependency of the highlighter; its consumers do not need to install
this package separately. The existing `default.css`, `base.css` and
`languages/typescript.css` package paths remain available through exports.

## Consumer entry points

```ts
import "@nsh/highlighter/themes.css"; // All three presets; preferred for a selector.
import { themes } from "@nsh/highlighter/themes"; // IDs, names and descriptions.
```

```html
<main data-nsh-preset="muted" data-nsh-theme="dark">
  <!-- Rendered .nsh code blocks -->
</main>
```

`data-nsh-preset` selects Default / Muted / Contrast. The existing
`data-nsh-theme` selects light/dark. Explicit `data-nsh-preset` and `data-theme`
on a `.nsh` block override the ancestor preset and mode respectively. Preset
contexts inherit, so a nested preset can choose its own palette.

To ship a single registered preset, import
`@nsh/highlighter/themes/muted.css` and set `data-nsh-preset="muted"`.
`@nsh/highlighter/theme.css` remains the self-contained Default entry. Omitting a
preset uses Default. Switching requires only CSS attributes, not model inference.

Public `--nsh-*` variables are consumer overrides and take priority over base and
language colors. Internal `--_nsh-*` variables implement the generated palettes;
applications should not depend on them. Font, spacing, padding and borders remain
application CSS, not preset data.

Embedded spans carry optional `documentKind` metadata, rendered as
`data-nsh-language`, so CSS inside Vue/HTML can use a selector palette while their
JS/TS spans use type colors. This context is added by composition and does not
change model weights, token types, offsets or modifiers.

The common palette also covers PHP's `trait` and `constant` roles, using type and
enum-member color families across all light/dark presets. Consumer overrides use
`--nsh-trait` and `--nsh-constant` with the usual optional style suffixes.

Markdown adds shared `heading`, `link`, `link-destination`, `code`, `code-fence`,
`code-language` and `embedded-code` roles to all six preset/mode palettes. Heading
weight and link underline follow their role styles. Nested `strong`, `emphasis`
and `strikethrough` modifiers additionally use `--nsh-strong-font-weight`,
`--nsh-emphasis-font-style` and `--nsh-strikethrough-text-decoration` overrides.
These are semantic styles shared across languages; code-fence child spans keep
their actual `data-nsh-language` and existing language colors.
