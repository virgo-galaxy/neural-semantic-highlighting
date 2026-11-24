# Neural Semantic Highlighting

[![CI](https://github.com/virgo-galaxy/virgo-nsh/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/virgo-galaxy/virgo-nsh/actions/workflows/ci.yml)
[![npm version](https://img.shields.io/npm/v/neural-semantic-highlighting)](https://www.npmjs.com/package/neural-semantic-highlighting)
[![MIT License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Semantic highlighting for source code and file formats. NSH runs ONNX inference
in a browser Web Worker and returns escaped HTML and semantic spans.

[Try the live Playground](https://nsh.virgogalaxy.com/) ·
[Quick start](#quick-start) ·
[React, Vue and vanilla JS](#react-vue-and-vanilla-javascript) ·
[Model deployment](#model-deployment) ·
[Themes and custom CSS](#light--dark-themes-and-custom-css) ·
[Supported languages and formats](#supported-code-languages-file-formats-and-measured-quality)

## Quick start

### Install from npm

In your frontend project, install the published package. The examples use Vite
to build the JavaScript, Web Worker and WebAssembly assets.

```bash
npm install neural-semantic-highlighting
```

### Serve the matching models

The npm package contains the highlighter and themes. Your app serves the model
weights (`.onnx`) and their matching metadata (`.json`). The browser downloads
each model on first use, and your source code stays in the browser.

For `0.1.0`, download and unpack the
[matching source snapshot](https://github.com/virgo-galaxy/virgo-nsh/archive/7109bac49340b94ad5350778e32ee0d4196c5698.tar.gz).
For another version, use the source snapshot linked in that version's npm README.
From the unpacked snapshot, run these commands with Node.js 24 and pnpm 11:

```bash
pnpm install --frozen-lockfile
pnpm build:packages
node scripts/export-model-assets.mjs --models typescript,css
```

This exports two model families. `typescript` serves JavaScript, TypeScript, JSX
and TSX. `css` serves CSS, SCSS and Less. From your **frontend project's root**,
copy the export into Vite's public assets:

```bash
mkdir -p public/models
cp -R /path/to/unpacked-snapshot/artifacts/browser/models/. public/models/
```

Keep the `v1/` directory and its filenames intact. Vite serves these files under
`/models/` in development and copies them into the production build.

### Highlight code

For a plain Vite page, add this to `index.html`:

```html
<div id="example">
  <pre class="nsh"><code></code></pre>
</div>
<script type="module" src="/main.js"></script>
```

Create `main.js` next to `index.html`:

```js
import { createHighlighter } from "neural-semantic-highlighting";
import "neural-semantic-highlighting/theme.css";

const highlighter = createHighlighter({
  modelBaseUrl: "/models/",
  languages: ["tsx", "scss"],
});

const source = "const App = () => <button>Hello</button>;";
const example = document.querySelector("#example");
example.querySelector("code").textContent = source;

try {
  const { html } = await highlighter.highlight(source, { language: "tsx" });
  example.innerHTML = html;
} catch (error) {
  console.error("Could not highlight the example", error);
}
```

Run `npx vite` and open the URL it prints. Use HTTPS or localhost in a modern
browser with module Workers, WebAssembly SIMD and Web Crypto. Run inference on
the client and pass a content ID such as `tsx` or `scss` explicitly. Reuse the
highlighter across code blocks, then call `highlighter.close()` when the app
is done with it.

## React, Vue and vanilla JavaScript

Each full example keeps plain code visible while models load or if highlighting
fails. The React and Vue components also discard obsolete results when props change.

| Frontend           | Integration guide                        | Complete example                                                                                       |
| ------------------ | ---------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| React + TypeScript | [React](examples/react/README.md)        | [CodeBlock.tsx](examples/react/CodeBlock.tsx)                                                          |
| Vue 3 + TypeScript | [Vue](examples/vue/README.md)            | [CodeBlock.vue](examples/vue/CodeBlock.vue)                                                            |
| HTML and JS        | [Vanilla JS](examples/vanilla/README.md) | [HTML](examples/vanilla/index.html), [JS](examples/vanilla/main.js), [CSS](examples/vanilla/style.css) |

For React and Vue, copy the [shared initializer](examples/highlighter-remote.ts)
to `src/highlighter.ts`. Copy the appropriate `CodeBlock` file to
`src/components/`. Both examples use the same `/models/` setup as the quick start.

**React** renders NSH output after the component mounts:

```tsx
import { CodeBlock } from "./components/CodeBlock";

export default function App() {
  return <CodeBlock code={"const App = () => <button>Hello</button>;"} language="tsx" />;
}
```

**Vue** uses the same initializer and props:

```vue
<script setup lang="ts">
import CodeBlock from "./components/CodeBlock.vue";
</script>

<template>
  <CodeBlock code=".card { &:hover { color: red; } }" language="scss" />
</template>
```

**Vanilla JS** can highlight an existing code element. Use the same
`highlighter` from the quick start and add a `language-*` class:

```html
<pre><code id="example" class="language-tsx">const App = () =&gt; &lt;button&gt;Hello&lt;/button&gt;;</code></pre>
```

```js
await highlighter.highlightElement(document.querySelector("#example"));
```

`highlightElement` also accepts an explicit `{ language: "tsx" }` option or reads
the element's `data-language` attribute. The [vanilla guide](examples/vanilla/README.md)
shows how to run the complete example with Vite.

### Render the result

| Field    | Use it for                                                                |
| -------- | ------------------------------------------------------------------------- |
| `html`   | A complete `<pre class="nsh"><code>…</code></pre>` block                  |
| `value`  | Escaped token markup to put inside an existing `<code>` element           |
| `result` | Theme-independent semantic spans with offsets in the original UTF-16 text |

## Model deployment

| Where the files live                                | Configuration                                                                |
| --------------------------------------------------- | ---------------------------------------------------------------------------- |
| Your website, with selected models in public assets | `modelBaseUrl: "/models/"`                                                   |
| A separate static host or object store              | `modelBaseUrl: "https://assets.example.com/models/"` with cross-origin reads |
| Private storage                                     | A `resolveAssetUrl` callback that returns a URL for each requested asset     |

With a separate host, allow browser `GET` requests from your app's origin for
both the ONNX and JSON files. See the [model delivery guide](docs/model-delivery.md)
for asset paths, CORS and signed URLs.

Export only the model families your app needs, and configure `languages` with the
content IDs your app offers. For example, export `typescript,css` and register
`["tsx", "scss"]`. The exporter includes required child models for composed
content such as HTML and Vue. Omit `--models` when exporting and omit `languages`
when initializing to offer the full catalog. Models still download on first use.

## Assets and performance

- The current ONNX files are about **3.6 MB each** before HTTP compression. The
  shared WASM asset is about **14.8 MB** uncompressed. First-use latency includes
  downloads, integrity checks and model initialization.
- Verified models use a best-effort **64 MB** browser cache by default. Each
  Worker keeps up to **4 model sessions** and releases idle sessions as languages
  change. Downloads time out after **30 seconds**. See [model caching](docs/model-cache.md)
  for the settings and loading errors.

## Content types, names and aliases

Use a content ID or alias such as `typescript` / `ts` or `yaml` / `yml`.
Aliases are case-insensitive. Use the model ID from the
[support tables](#supported-code-languages-file-formats-and-measured-quality)
when exporting assets. For example, pass `tsx` to `highlight` and `typescript`
to the exporter. To inspect the configured highlighter, call
`highlighter.supports("tsx")` or `highlighter.languages()`.

Use the metadata-only catalog to build a selector without importing the Worker,
WASM or models:

```ts
import {
  contentCategories,
  contentTypes,
  getContentType,
} from "neural-semantic-highlighting/catalog";

getContentType("tsx")?.modelId; // "typescript"
getContentType("yml")?.category; // "formats"
```

See [content organization](docs/content-organization.md) for IDs, aliases and
filename metadata.

## Light / dark themes and custom CSS

### Choose a theme style independently of light / dark

Three built-in presets are available:

| ID         | Name     | Direction                                                            |
| ---------- | -------- | -------------------------------------------------------------------- |
| `default`  | Default  | Cool neutral surfaces with violet, lake blue, jade and amber accents |
| `muted`    | Muted    | Warm neutral surfaces and restrained green, plum and blue accents    |
| `contrast` | Contrast | Black/white surfaces with strong, distinct semantic colors           |

For a theme selector, import all presets once:

```ts
import "neural-semantic-highlighting/themes.css";
import { themes } from "neural-semantic-highlighting/themes";
// themes contains { id, name, description } for each preset.
```

Select the style and mode on an ancestor of the rendered code:

```html
<main data-nsh-preset="muted" data-nsh-theme="dark">
  <!-- Code blocks -->
</main>
```

```ts
document.documentElement.dataset.nshPreset = "contrast";
document.documentElement.dataset.nshTheme = "light";
```

The Playground offers the same independent controls: a **Code theme** selector and
light/dark buttons. It retains workspace dependencies and browser inference.
Neither palette switching nor mode switching reruns the model.

To include only one preset, use `neural-semantic-highlighting/themes/muted.css` and select
`data-nsh-preset="muted"`. Import the corresponding CSS before selecting a
preset; importing the metadata catalog alone does not load styles.

Set `data-nsh-preset` directly on `.nsh` to override an ancestor's style:

```html
<pre class="nsh" data-nsh-preset="contrast" data-theme="light"><code>...</code></pre>
```

Each preset contains its own complete light/dark base palette and optional
language adjustments. CSS/SCSS/Less selectors and JS/TS/JSX/TSX types can have
suitable accents within the same theme. Other languages inherit the selected
preset's base. Embedded HTML/Vue spans retain their child-language context for
these adjustments. Your public `--nsh-*` overrides have the final say.

Theme JSON files, validation and CSS generation are documented in
[packages/themes/web](packages/themes/web/README.md). They are development assets;
consumers use the generated CSS directly.

### Import the default theme once

```ts
import "neural-semantic-highlighting/theme.css";
```

This existing entry includes the Default preset with light and dark palettes.
Without a theme attribute, the default is
light. Colors are CSS variables, not model output: switching themes immediately
restyles existing spans without calling `highlight` again.

### Follow your application's theme

Put `data-nsh-theme` on `<html>` or an ancestor of the code blocks:

```html
<html data-nsh-theme="light"></html>
```

When the application switches theme, update the same attribute on the client:

```ts
function setTheme(theme: "light" | "dark") {
  document.documentElement.dataset.nshTheme = theme;
}
setTheme("dark"); // Change to "light" for the light palette.
```

React and Vue can also bind the attribute on their application wrapper:

```tsx
<main data-nsh-theme={theme}>{/* React code blocks */}</main>
```

```vue
<main :data-nsh-theme="theme"><!-- Vue code blocks --></main>
```

NSH does not detect an application's existing `.dark`, `data-theme` or theme
store automatically. Mirror that application's current `"light"`/`"dark"` value
onto `data-nsh-theme` in its theme-switch handler or reactive binding.

### Set or override one code block

Set `data-theme` directly on the rendered `.nsh` element:

```html
<pre class="nsh" data-theme="dark"><code>...</code></pre>
<pre class="nsh" data-theme="light"><code>...</code></pre>
```

A block's explicit `data-theme` takes precedence over the ancestor's
`data-nsh-theme`. For `result.html`, set the attribute on the inserted `.nsh`
element. For the React/Vue wrappers above, add `data-theme` directly to their
`<pre>` when a fixed per-block theme is wanted.

### Optionally follow the operating system

For an app without its own theme preference, run this once on the client:

```js
const preference = window.matchMedia("(prefers-color-scheme: dark)");
const syncTheme = () => {
  document.documentElement.dataset.nshTheme = preference.matches ? "dark" : "light";
};
syncTheme();
preference.addEventListener("change", syncTheme);
// When disposing the application:
// preference.removeEventListener("change", syncTheme);
```

This is an optional application recipe, not an automatic behavior of the library.
If the app already has a user-selected theme, use that theme as the source of truth.

### Customize colors, fonts and layout

Import your **global** stylesheet after the default theme:

```ts
import "neural-semantic-highlighting/theme.css";
import "./theme.css";
```

For the React/Vue shared initializer, add `import "./theme.css"` after the default
theme import in `src/highlighter.ts`. Start with
[examples/theme.css](examples/theme.css) as `src/theme.css`:

```css
/* Load after the default theme. These are example application colors. */
.nsh {
  --nsh-background: #fafafa;
  --nsh-foreground: #24292f;
  --nsh-keyword: #8250df;
  --nsh-string: #0a3069;
  --nsh-comment: #57606a;
  --nsh-number: #0550ae;
  --nsh-function: #8250df;

  padding: 16px;
  border-radius: 8px;
  overflow: auto;
  font:
    14px/1.6 ui-monospace,
    monospace;
}
.nsh[data-theme="dark"],
[data-nsh-theme="dark"] .nsh:not([data-theme="light"]) {
  --nsh-background: #18181b;
  --nsh-foreground: #fafafa;
  --nsh-keyword: #c084fc;
  --nsh-string: #a5d6ff;
  --nsh-comment: #a1a1aa;
  --nsh-number: #79c0ff;
  --nsh-function: #d2a8ff;
}
```

The `.nsh` rule supplies your light/default values. The second rule supplies your
dark values and respects an explicitly light block inside a dark app. Only
variables you override change; other token colors keep their built-in defaults.
Library selectors use `:where(...)`, so ordinary application selectors can
override the palette and language defaults without `!important`.

| Variable                                | Controls                             |
| --------------------------------------- | ------------------------------------ |
| `--nsh-background` / `--nsh-foreground` | Code-block background / default text |
| `--nsh-keyword`                         | Keywords                             |
| `--nsh-comment`                         | Comments                             |
| `--nsh-string`                          | Strings and entities                 |
| `--nsh-number`                          | Numbers                              |
| `--nsh-regexp`                          | Regular expressions                  |
| `--nsh-function` / `--nsh-method`       | Functions / methods                  |
| `--nsh-type` / `--nsh-class`            | Types / classes                      |
| `--nsh-tag` / `--nsh-attribute`         | Tags / attributes                    |
| `--nsh-operator` / `--nsh-punctuation`  | Operators / punctuation              |

Diff/Patch uses `--nsh-addition` and `--nsh-deletion` for whole changed-line
foreground colors in every preset/mode. Original `+` and `-` signs stay visible.
Override these variables like other semantic colors. To add your own line
background, target `.nsh [data-token-type="addition"]` or
`.nsh [data-token-type="deletion"]` in ordinary application CSS.

For individual semantic styles, target the rendered attributes:

```css
.nsh [data-token-type="comment"] {
  font-style: normal;
}
.nsh [data-modifiers~="deprecated"] {
  text-decoration: line-through;
}
```

In Vue, put these rules in a global stylesheet. A component's `<style scoped>`
does not automatically reach token elements inserted by `v-html`; use `:deep()`
for those token selectors if you keep them scoped. Setting `--nsh-*` on the
component's own `<pre class="nsh">` also works through variable inheritance.

<a id="supported-languages-and-measured-quality"></a>

## Supported code languages, file formats and measured quality

There are **40 model packs**, with browser inference and Playground examples.
Some source kinds share weights, including XML/SVG and JSON/JSONC; Flutter shares Dart.
The browser conversion preserves the selected weights without retraining or
quantization. The latest [verification record](docs/diff-browser-verification.json)
retains **410/410** exact browser/native comparisons and **180** passing frontend
tests. Independent local-package checks cover public imports, original source
text, themes and custom CSS. [Browser verification](docs/browser-runtime.md)
keeps the earlier rollout results separately. These are runtime/packaging checks,
not a new accuracy evaluation.

All selected models use **512 UTF-8 bytes per inference window**. Longer documents
are processed in multiple windows; 512 bytes is not a file-size limit.

**Parameters** is the selected model's parameter count. **ONNX size** is its
uncompressed browser `.onnx` file size, with **1 MB = 1,000,000 bytes**. Each row
counts only that model, excluding the shared runtime, JS/CSS and any child-model
dependencies used for composed highlighting. See [model deployment](#model-deployment)
for how to ship a subset of models.

The tables report **exact-span F1**: token start, end and semantic type must match.
It is not character accuracy or the percentage of perfect files. Different test
sets and sample sizes are not directly comparable. Reports retain known limits.

### Code languages

[Full support details and measured limits](docs/code-languages.md).

| Name                                                        | Accepted content IDs / aliases                         | Model        | Parameters | ONNX size | Measured test exact-span F1                                                                                                      |
| ----------------------------------------------------------- | ------------------------------------------------------ | ------------ | ---------: | --------: | -------------------------------------------------------------------------------------------------------------------------------- |
| [JavaScript / TypeScript](packs/typescript/model/README.md) | `typescript`, `ts`, `javascript`, `js`, `jsx`, `tsx`   | `typescript` |    897,833 |  3.614 MB | [99.45%; real TSX 99.39%](packs/typescript/model/BENCHMARKS.md) — exposed 50-file regression; first-read 24-file product cohort  |
| [Go](packs/go/model/README.md)                              | `go`                                                   | `go`         |    894,614 |  3.601 MB | [99.03%](packs/go/model/README.md#selected-candidate) — natural test                                                             |
| [CSS / SCSS / Less](packs/css/model/README.md)              | `css`, `scss`, `less`                                  | `css`        |    894,227 |  3.599 MB | [CSS 99.04%; SCSS 99.40%; Less 99.42%](packs/css/model/BENCHMARKS.md) — natural test, per language                               |
| [HTML](packs/html/model/README.md)                          | `html`                                                 | `html`       |    893,711 |  3.597 MB | [Markup 96.37%; composed 96.53%](packs/html/model/BENCHMARKS.md) — natural test, separate scopes                                 |
| [Vue](packs/vue/model/README.md)                            | `vue`                                                  | `vue`        |    894,485 |  3.600 MB | [97.12%](packs/vue/model/BENCHMARKS.md) — natural composed test; profile results are separate in the report                      |
| [Python](packs/python/model/README.md)                      | `python`, `py`                                         | `python`     |    895,398 |  3.607 MB | [91.48%](packs/python/model/BENCHMARKS.md) — exposed 4-file regression; additional 19 files 90.87% (separate cohort)             |
| [Shell](packs/bash/model/README.md)                         | `bash`, `sh`, `shell`, `zsh`, `csh`, `tcsh`            | `bash`       |    894,366 |  3.602 MB | [87.12%](packs/bash/model/BENCHMARKS.md) — exposed 11-file regression; Bash 94.29%; additional 12 files 90.91% (separate cohort) |
| [Perl](packs/perl/model/README.md)                          | `perl`                                                 | `perl`       |    894,995 |  3.603 MB | [91.00%](packs/perl/model/BENCHMARKS.md) — exposed 4-file regression; additional 16 files 88.33% (separate cohort)               |
| [AWK](packs/awk/model/README.md)                            | `awk`                                                  | `awk`        |    893,582 |  3.596 MB | [96.89%](packs/awk/model/BENCHMARKS.md) — natural test                                                                           |
| [SQL](packs/sql/model/README.md)                            | `sql`                                                  | `sql`        |    894,737 |  3.602 MB | [90.08%](packs/sql/model/BENCHMARKS.md) — exposed 7-file regression                                                              |
| [PowerShell](packs/powershell/model/README.md)              | `powershell`, `pwsh`, `ps1`                            | `powershell` |    894,737 |  3.602 MB | [91.96%](packs/powershell/model/BENCHMARKS.md) — exposed 3-file regression                                                       |
| [BAT / CMD](packs/bat/model/README.md)                      | `bat`, `cmd`                                           | `bat`        |    894,350 |  3.600 MB | [90.61%](packs/bat/model/BENCHMARKS.md) — exposed 3-file regression; additional 6 files 75.36% (separate cohort)                 |
| [Assembly](packs/assembly/model/README.md)                  | `assembly`, `asm`, `nasm`, `masm`, `gas`               | `assembly`   |    893,711 |  3.597 MB | [98.63%](packs/assembly/model/BENCHMARKS.md) — natural test, 5 files; per-profile results in report                              |
| [Java](packs/java/model/README.md)                          | `java`                                                 | `java`       |    895,382 |  3.604 MB | [93.59%](packs/java/model/BENCHMARKS.md) — exposed 29-file regression                                                            |
| [C#](packs/csharp/model/README.md)                          | `csharp`, `cs`, `c#`                                   | `csharp`     |    895,511 |  3.605 MB | [95.53%](packs/csharp/model/BENCHMARKS.md) — exposed 24-file regression                                                          |
| [C](packs/c/model/README.md)                                | `c`                                                    | `c`          |    894,227 |  3.599 MB | [94.60%](packs/c/model/BENCHMARKS.md) — exposed 18-file regression                                                               |
| [C++](packs/cpp/model/README.md)                            | `cpp`, `c++`, `cxx`                                    | `cpp`        |    895,511 |  3.605 MB | [94.16%](packs/cpp/model/BENCHMARKS.md) — exposed 14-file regression                                                             |
| [PHP](packs/php/model/README.md)                            | `php`                                                  | `php`        |    895,898 |  3.606 MB | [95.55%](packs/php/model/BENCHMARKS.md) — exposed 21-file regression                                                             |
| [Svelte](packs/svelte/model/README.md)                      | `svelte`                                               | `svelte`     |    895,398 |  3.607 MB | [91.41%](packs/svelte/model/BENCHMARKS.md) — exposed 9-file regression                                                           |
| [Rust](packs/rust/model/README.md)                          | `rust`, `rs`                                           | `rust`       |    895,511 |  3.605 MB | [95.93%](packs/rust/model/BENCHMARKS.md) — exposed 15-file regression                                                            |
| [Zig](packs/zig/model/README.md)                            | `zig`                                                  | `zig`        |    894,485 |  3.600 MB | [93.65%](packs/zig/model/BENCHMARKS.md) — exposed 21-file regression                                                             |
| [Dart / Flutter](packs/dart/model/README.md)                | `dart`, `flutter`                                      | `dart`       |    894,872 |  3.602 MB | [95.07%](packs/dart/model/BENCHMARKS.md) — exposed 20-file regression                                                            |
| [Swift](packs/swift/model/README.md)                        | `swift`                                                | `swift`      |    894,872 |  3.602 MB | [94.52%](packs/swift/model/BENCHMARKS.md) — exposed 22-file regression                                                           |
| [Kotlin](packs/kotlin/model/README.md)                      | `kotlin`, `kt`, `kts`, `kotlin-script`                 | `kotlin`     |    895,640 |  3.605 MB | [96.28%](packs/kotlin/model/BENCHMARKS.md) — exposed 31-file regression                                                          |
| [R](packs/r/model/README.md)                                | `r`                                                    | `r`          |    894,872 |  3.602 MB | [96.04%](packs/r/model/BENCHMARKS.md) — natural test, 15 files                                                                   |
| [Scala](packs/scala/model/README.md)                        | `scala`                                                | `scala`      |    895,656 |  3.608 MB | [90.23%](packs/scala/model/BENCHMARKS.md) — exposed 30-file regression                                                           |
| [Ruby](packs/ruby/model/README.md)                          | `ruby`, `rb`, `rake`, `gemspec`, `gemfile`, `rakefile` | `ruby`       |    895,656 |  3.608 MB | [90.60%](packs/ruby/model/BENCHMARKS.md) — exposed 15-file regression; additional 11 files 94.41% (separate cohort)              |
| [Lua](packs/lua/model/README.md)                            | `lua`                                                  | `lua`        |    895,640 |  3.605 MB | [94.36%](packs/lua/model/BENCHMARKS.md) — exposed 15-file regression                                                             |
| [GraphQL](packs/graphql/model/README.md)                    | `graphql`, `gql`                                       | `graphql`    |    895,124 |  3.603 MB | [96.36%](packs/graphql/model/BENCHMARKS.md) — 14 natural test files                                                              |

### File formats

[Full support details and measured limits](docs/file-formats.md).

| Name                                               | Accepted content IDs / aliases                            | Model        | Parameters | ONNX size | Measured test exact-span F1                                                                                      |
| -------------------------------------------------- | --------------------------------------------------------- | ------------ | ---------: | --------: | ---------------------------------------------------------------------------------------------------------------- |
| [JSON / JSONC](packs/json/model/README.md)         | `json`, `jsonc`                                           | `json`       |    894,872 |  3.602 MB | [Natural test](packs/json/model/BENCHMARKS.md): JSON 99.71% (9 files); JSONC 99.84% (6 files)                    |
| [YAML](packs/yaml/model/README.md)                 | `yaml`, `yml`                                             | `yaml`       |    894,872 |  3.602 MB | [95.34%](packs/yaml/model/BENCHMARKS.md) — natural test, 12 files                                                |
| [TOML](packs/toml/model/README.md)                 | `toml`                                                    | `toml`       |    894,872 |  3.602 MB | [99.10%](packs/toml/model/BENCHMARKS.md) — natural test, 9 files                                                 |
| [INI](packs/ini/model/README.md)                   | `ini`, `cfg`, `editorconfig`                              | `ini`        |    894,872 |  3.602 MB | [96.93%](packs/ini/model/BENCHMARKS.md) — exposed 8-file regression                                              |
| [.env](packs/dotenv/model/README.md)               | `dotenv`, `env`, `.env`                                   | `dotenv`     |    894,872 |  3.602 MB | [98.25%](packs/dotenv/model/BENCHMARKS.md) — natural test, 3 files                                               |
| [XML](packs/xml/model/README.md)                   | `xml`                                                     | `xml`        |    894,108 |  3.601 MB | [87.72%](packs/xml/model/BENCHMARKS.md) — exposed 7-file regression                                              |
| [SVG](packs/xml/model/README.md)                   | `svg`                                                     | `xml`        |    894,108 |  3.601 MB | [100.00%](packs/xml/model/BENCHMARKS.md) — exposed 6-file regression                                             |
| [Markdown](packs/markdown/model/README.md)         | `markdown`, `md`, `mdown`, `mkd`                          | `markdown`   |    894,227 |  3.599 MB | [95.10%](packs/markdown/model/BENCHMARKS.md) — new independent natural test, 20 files                            |
| [Dockerfile](packs/dockerfile/model/README.md)     | `dockerfile`, `docker`, `containerfile`                   | `dockerfile` |    893,969 |  3.598 MB | [96.33%](packs/dockerfile/model/BENCHMARKS.md) — independent natural test, 14 files                              |
| [Makefile](packs/makefile/model/README.md)         | `makefile`, `make`, `mk`, `mak`, `gnumake`, `gnumakefile` | `makefile`   |    894,479 |  3.601 MB | [94.12%](packs/makefile/model/BENCHMARKS.md) — exposed 17-file regression; historical additional 16 files 94.57% |
| [Protocol Buffers](packs/protobuf/model/README.md) | `protobuf`, `proto`, `protocol-buffers`                   | `protobuf`   |    894,995 |  3.603 MB | [98.55%](packs/protobuf/model/BENCHMARKS.md) — 12 fresh natural test files                                       |
| [Diff / Patch](packs/diff/model/README.md)         | `diff`, `patch`, `udiff`, `unified-diff`, `git-diff`      | `diff`       |    893,963 |  3.599 MB | [98.03%](packs/diff/model/BENCHMARKS.md) — 26 natural test patches                                               |

The 2026-11-19 revisions report exposed historical regressions separately from
additional frozen-family tests. Targets of 90%/95% are goals, not guarantees:
Perl's additional namespace files and BAT's harder project holdout remain below
90%. See each report's role macro, Golden and dialect details. Earlier complete
inference bundles remain under `packs/<name>/model-20261119-v1` and the matching
browser archives; external data and full training experiments remain preserved.
Selected overlapping windows can improve long-file edges with additional browser
inference cost; short snippets keep the existing single-window path.

Previously recorded HTML/Vue/PHP/Markdown composed scores refer to their archived
child-model revisions. A changed JS/TS child requires a new composed measurement;
base-model scores and browser/native consistency are separate evidence.

## Development and training

Run the browser Playground from this checkout with Node.js 24 and pnpm 11:

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Open <http://127.0.0.1:3000/>. The [Playground build and model loading guide](docs/playground-model-loading.md)
describes how the live demo serves assets and updates the preview while you edit.

### Bundle selected models in workspace builds

For local development with `@nsh/*` packages, see the
[workspace archive and model descriptor guide](docs/model-delivery.md#install-workspace-archives).
It includes a verified TSX/SCSS build that ships only the TypeScript and CSS model
families.

### Training and verification

External training data lives at
`~/Datasets/neural-semantic-highlighting/<model-name>/`. Set `NSH_DATASET_ROOT` to
use a different parent directory.

See [development](docs/development.md) for workspace checks, native reference
inference, datasets and checkpoint continuation. See
[browser export and verification](training/browser/README.md) for reproducible
ONNX conversion and [portable release metadata](docs/portable-release.md) for
the `pnpm check:portable` scope.

## License

The [MIT License](LICENSE) covers project-authored source code and documentation.
Review the applicable terms separately for model weights and third-party
materials. Third-party license notices apply to their respective components.
