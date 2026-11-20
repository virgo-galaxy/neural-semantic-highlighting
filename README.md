# Neural Semantic Highlighting

Neural highlighting for source code and file formats in frontend applications.
Import a highlighter, pass text and its content type, and render the returned HTML. Inference runs locally
in a browser Web Worker using the existing models; consumers need no Python
process, language SDK or highlighting server.

**Distribution status:** this repository and all packages are still private.
`@nsh/highlighter` is the current package name in this workspace, **not a package
already published on npm**. Local tarball installation works today. Publication
and repository visibility are separate release decisions.

[Install](#try-it-now) · [Simple usage](#simple-integration-react-vue-and-vanilla-javascript) ·
[Complete examples](#complete-integration-examples) ·
[Themes and custom CSS](#light--dark-themes-and-custom-css) ·
[Content types and aliases](#content-types-names-and-aliases)

## Try it now

From this checkout, with Node.js 24 and pnpm 11:

```bash
pnpm install
pnpm dev
```

Open <http://127.0.0.1:3000/>. The Playground uses browser inference, including in
its production build. It does not start the Python provider.

To install the built packages into another frontend project before publication:

```bash
# In this repository; output goes to artifacts/browser/npm/.
pnpm pack:browser

# In the consuming project; use the actual path to this checkout.
npm install /path/to/neural-semantic-highlighting/artifacts/browser/npm/*.tgz
```

This installs the highlighter, its three internal dependencies and the optional
`@nsh/models` resource package from local archives. Use an ESM frontend bundler; Vite production builds have been verified.
Other bundlers have not yet been verified. No alias into this repository, Python
setup, special Vite bridge or manual model URL configuration is required.

## Highlight code

```ts
import { createHighlighter } from "@nsh/highlighter";
import css from "@nsh/models/languages/css";
import typescript from "@nsh/models/languages/typescript";
import "@nsh/highlighter/theme.css";

// Create once and reuse: models are fetched on first use, then kept in the worker.
const highlighter = createHighlighter({ languages: [typescript, css] });
const result = await highlighter.highlight("export const App = () => <button>Hello</button>;", {
  language: "tsx",
});

document.querySelector("#example")!.innerHTML = result.html;
```

`html` contains a complete `<pre class="nsh"><code>…</code></pre>` block. `value`
contains only escaped token markup for an existing code element. `result` contains
theme-independent semantic spans with original UTF-16 offsets. Source text and
attribute values are escaped by the renderer.

Unlike a synchronous highlighter, `highlight` returns a Promise. Show ordinary
code while it loads, and ignore obsolete results when the source changes. Pass an
explicit language; automatic language detection is not implemented. This is a
frontend highlighting alternative, not a complete drop-in implementation of the
highlight.js API.

For an existing element:

```html
<pre><code class="language-tsx">const App = () =&gt; &lt;div /&gt;;</code></pre>
```

```ts
await highlighter.highlightElement(document.querySelector("code")!);
// Also accepts { language: "tsx" } or an element's data-language attribute.
```

Use `highlighter.supports("tsx")` and `highlighter.languages()` to inspect support.
Call `highlighter.close()` when the application no longer needs this instance;
this terminates its worker and rejects pending requests. Create a new instance to
start again. Module imports are safe during SSR, but call inference on the client.

## Simple integration: React, Vue and vanilla JavaScript

All three use the same asynchronous `highlighter.highlight(code, { language })`
API. React and Vue have comparable integration steps. The short framework
examples below use the complete `CodeBlock` components shown in the next section;
they are application components you copy, not exports from the npm package.

### React: simple usage

After copying the shared initializer and React component below, in `src/App.tsx`:

```tsx
import { CodeBlock } from "./components/CodeBlock";

export default function App() {
  return <CodeBlock code={"const answer = 42;"} language="typescript" />;
}
```

### Vue 3: simple usage

After copying the same shared initializer and Vue component below, in `src/App.vue`:

```vue
<script setup lang="ts">
import CodeBlock from "./components/CodeBlock.vue";
const source = "const answer = 42;";
</script>

<template>
  <CodeBlock :code="source" language="typescript" />
</template>
```

### Vanilla JavaScript: simple usage

Use ordinary HTML with an ESM entry (`<script type="module" src="./main.js"></script>`)
and a `<div id="example"></div>`:

```js
import { createHighlighter } from "@nsh/highlighter";
import css from "@nsh/models/languages/css";
import typescript from "@nsh/models/languages/typescript";
import "@nsh/highlighter/theme.css";

const highlighter = createHighlighter({ languages: [typescript, css] });
const { html } = await highlighter.highlight("const answer = 42;", { language: "javascript" });
document.querySelector("#example").innerHTML = html;
```

Vanilla JS means no React or Vue dependency. The current npm modules still need
an ESM bundler to resolve package imports and emit Worker/model/WASM assets.
The complete example below uses Vite. A direct CDN `<script src>` distribution
without a build step is not currently provided.

## Complete integration examples

Install the local packages as described above. The React and Vue examples assume
an existing TypeScript frontend project; keep its normal framework/Vite setup.
Both handle loading, errors, changing source/language, obsolete asynchronous
results and component unmounting. Ordinary escaped code remains visible while
inference loads or fails. No framework adapter package is required.

### Shared React / Vue initializer

Create `src/highlighter.ts` from [examples/highlighter.ts](examples/highlighter.ts):

```ts
import "@nsh/highlighter/theme.css";

import { createHighlighter } from "@nsh/highlighter";
import css from "@nsh/models/languages/css";
import typescript from "@nsh/models/languages/typescript";

// One worker and model cache for the whole client application.
export const highlighter = createHighlighter({ languages: [typescript, css] });
```

Both components reuse this application-level instance. They stop updating after
unmount, while the shared worker remains available to other code blocks. Call
`highlighter.close()` only when the whole application no longer needs it, not
when one shared code block unmounts. Create a new instance after closing.

### React: complete component

Copy [examples/react/CodeBlock.tsx](examples/react/CodeBlock.tsx) to
`src/components/CodeBlock.tsx`, then use the short React example above:

```tsx
import { useEffect, useState } from "react";

import { highlighter } from "../highlighter";

type Highlighted = { code: string; language: string; value?: string; error?: string };

export function CodeBlock({ code, language }: { code: string; language: string }) {
  const [result, setResult] = useState<Highlighted>();
  useEffect(() => {
    let active = true;
    highlighter.highlight(code, { language }).then(
      ({ value }) => {
        if (active) setResult({ code, language, value });
      },
      (reason: unknown) => {
        if (active) setResult({ code, language, error: String(reason) });
      },
    );
    return () => {
      active = false;
    };
  }, [code, language]);
  const current = result?.code === code && result.language === language ? result : undefined;
  return (
    <>
      <pre className="nsh" data-language={language} aria-busy={current === undefined}>
        {current?.value === undefined ? (
          <code>{code}</code>
        ) : (
          <code dangerouslySetInnerHTML={{ __html: current.value }} />
        )}
      </pre>
      {current?.error ? <p role="alert">{current.error}</p> : null}
    </>
  );
}
```

React's `useEffect` starts inference on the client. For Next.js App Router, add
`"use client"` at the top of this component. The `value` passed to
`dangerouslySetInnerHTML` comes from the escaping NSH renderer.

### Vue 3: complete component

Copy [examples/vue/CodeBlock.vue](examples/vue/CodeBlock.vue) to
`src/components/CodeBlock.vue`, then use the short Vue example above:

```vue
<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch, type WatchStopHandle } from "vue";

import { highlighter } from "../highlighter";

const props = defineProps<{ code: string; language: string }>();
const markup = ref<string>();
const error = ref("");
let stopWatching: WatchStopHandle | undefined;

// Start inference on the client, after hydration.
onMounted(() => {
  stopWatching = watch(
    () => [props.code, props.language] as const,
    ([code, language], _, onCleanup) => {
      let active = true;
      onCleanup(() => {
        active = false;
      });
      markup.value = undefined;
      error.value = "";
      highlighter.highlight(code, { language }).then(
        ({ value }) => {
          if (active) markup.value = value;
        },
        (reason: unknown) => {
          if (active) error.value = String(reason);
        },
      );
    },
    { immediate: true },
  );
});
onBeforeUnmount(() => stopWatching?.());
</script>

<template>
  <pre
    class="nsh"
    :data-language="language"
    :aria-busy="markup === undefined && !error"
  ><code v-if="markup !== undefined" v-html="markup"></code><code v-else>{{ code }}</code></pre>
  <p v-if="error" role="alert">{{ error }}</p>
</template>
```

Vue's `onMounted` starts inference on the client; the watcher handles prop
changes. `v-html` receives only the renderer's escaped `value`. The extra lifecycle
code serves the same purpose as React's effect and cleanup. It is not an extra
model setup requirement. The existing Vue Playground is another working consumer.

### Vanilla JavaScript: complete HTML / CSS / JS

Copy the three files from [examples/vanilla](examples/vanilla/README.md) into a
new directory. With the local package archives already built:

```bash
npm init -y
npm install /path/to/neural-semantic-highlighting/artifacts/browser/npm/*.tgz
npm install --save-dev vite@8.2.2
npx vite
```

Open the local URL Vite prints. Use `npx vite build` to produce static files in
`dist`; this server is a development/build tool, not a required inference service.
Deploy `dist` to ordinary static hosting. Only the NSH packages and Vite are
needed; no React/Vue, Python or language SDK is installed.

`index.html`:

```html
<!doctype html>
<html lang="en" data-nsh-theme="light">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>NSH — Vanilla JavaScript</title>
  </head>
  <body>
    <main>
      <h1>Code highlighting</h1>
      <button id="theme" type="button">Switch to dark</button>
      <label
        >Language
        <select id="language">
          <option value="typescript">TypeScript</option>
          <option value="javascript">JavaScript</option>
          <option value="css">CSS</option>
        </select>
      </label>
      <label for="source">Source code</label>
      <textarea id="source" rows="6" spellcheck="false">
const greeting = "Hello, Virgo!";
console.log(greeting);</textarea>
      <button id="highlight" type="button">Highlight</button>
      <p id="status" role="status"></p>
      <div id="preview" aria-busy="false"></div>
    </main>
    <script type="module" src="./main.js"></script>
  </body>
</html>
```

`main.js`:

```js
import "@nsh/highlighter/theme.css";
import "./style.css";

import { createHighlighter } from "@nsh/highlighter";
import css from "@nsh/models/languages/css";
import typescript from "@nsh/models/languages/typescript";

const highlighter = createHighlighter({ languages: [typescript, css] });
const source = document.querySelector("#source");
const language = document.querySelector("#language");
const preview = document.querySelector("#preview");
const status = document.querySelector("#status");
const themeButton = document.querySelector("#theme");
let revision = 0;

function showPlainCode() {
  const pre = document.createElement("pre");
  pre.className = "nsh";
  pre.dataset.language = language.value;
  const code = document.createElement("code");
  code.textContent = source.value;
  pre.append(code);
  preview.replaceChildren(pre);
}

function invalidate() {
  revision += 1;
  showPlainCode();
  preview.setAttribute("aria-busy", "false");
  status.textContent = "Ready to highlight";
}

async function highlight() {
  const request = ++revision;
  showPlainCode();
  preview.setAttribute("aria-busy", "true");
  status.textContent = "Highlighting…";
  try {
    const { html } = await highlighter.highlight(source.value, { language: language.value });
    if (request !== revision) return;
    preview.innerHTML = html; // Escaped by the NSH renderer.
    status.textContent = "Highlighted";
  } catch (reason) {
    if (request !== revision) return;
    status.textContent = `Unable to highlight: ${String(reason)}`;
  } finally {
    if (request === revision) preview.setAttribute("aria-busy", "false");
  }
}

source.addEventListener("input", invalidate);
language.addEventListener("change", invalidate);
document.querySelector("#highlight").addEventListener("click", () => {
  void highlight();
});
themeButton.addEventListener("click", () => {
  const dark = document.documentElement.dataset.nshTheme !== "dark";
  document.documentElement.dataset.nshTheme = dark ? "dark" : "light";
  themeButton.textContent = dark ? "Switch to light" : "Switch to dark";
});

// Release the worker when leaving; restart normally if restored from back/forward cache.
window.addEventListener("pagehide", (event) => {
  if (!event.persisted) highlighter.close();
});
void highlight();
```

`style.css`:

```css
body {
  margin: 0;
  font-family: system-ui, sans-serif;
}
main {
  max-width: 800px;
  margin: 32px auto;
  padding: 0 16px;
}
label,
textarea {
  display: block;
  margin: 16px 0 8px;
}
textarea {
  box-sizing: border-box;
  width: 100%;
  font:
    14px/1.6 ui-monospace,
    monospace;
}
button,
select {
  padding: 6px 12px;
}

/* Load after @nsh/highlighter/theme.css. These are example application colors. */
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

This version includes editable source, language selection, safe plain-text
fallback, loading/errors and protection against obsolete results. The theme
button changes CSS attributes only; it does not rerun inference.

## Content types, names and aliases

Supported content is grouped as **Code languages** and **File formats**.
React JSX/TSX is covered by JavaScript/TypeScript, and Flutter reuses Dart.
Categories organize discovery; they do not determine which models are bundled.
Natural-language sentence analysis is not implemented.

Install/import paths use fixed package and model names. The existing
`language` option accepts catalog IDs and registered aliases, case-insensitively:
`javascript` / `js`, `typescript` / `ts`, `yaml` / `yml`, etc. An alias does
not create a second model or menu option. Filename variants such as `.d.ts`,
`.mts` and `.cjs` remain internal support metadata. The highlighter still
requires an explicit content type; it does not guess from text or filenames.

The metadata-only entry can populate a categorized selector without importing
models, WASM or a Worker:

```ts
import { contentCategories, contentTypes, getContentType } from "@nsh/highlighter/catalog";

getContentType("TS"); // TypeScript entry; modelId === "typescript"
getContentType("tsx"); // TSX entry; same modelId
getContentType("yml"); // YAML entry; category === "formats"
// contentTypes contains named content entries; aliases and filename variants
// are metadata rather than additional dropdown entries.
```

Existing imports such as `@nsh/highlighter/languages/typescript` remain valid
when the optional `@nsh/models` package is installed. The default highlighter
package no longer contains ONNX files; the separate resource package contains
all selected weights. Explicit imports control which assets enter your
application's production build. Remote model loading is not implemented yet.
See [content organization](docs/content-organization.md) for the catalog, paths
and framework-profile conventions.

## Load only the languages you need

The default entry requires explicit model selection and includes no ONNX files.
For a small production asset set, install the optional `@nsh/models` resource
package and select models explicitly:

```ts
import { createHighlighter } from "@nsh/highlighter";
import typescript from "@nsh/models/languages/typescript";
import css from "@nsh/models/languages/css";
import "@nsh/highlighter/theme.css";

const highlighter = createHighlighter({ languages: [typescript, css] });
await highlighter.highlight(source, { language: "tsx" });
```

Use `@nsh/highlighter/bundled` instead when deliberately including every local
model; it retains the zero-argument `createHighlighter()` convenience API and
requires `@nsh/models`. The shared React/Vue initializer and vanilla examples
select TypeScript and CSS; register additional models for other content types.

The TypeScript descriptor covers JS, TS, JSX and TSX. CSS covers CSS, SCSS and
Less. HTML and Vue descriptors automatically include the existing script/style
models they need. Composition uses neurally predicted embedded regions, not a
source parser. Tailwind classes remain string values.

Common language IDs: `javascript`, `typescript`, `jsx`, `tsx`, `go`, `css`, `scss`,
`less`, `html`, `vue`, `python`, `bash`, `zsh`, `csh`, `tcsh`, `sql`, `powershell`,
`bat`, `assembly`, `java`, `csharp`, `swift`, `kotlin`, `r`, `scala`, `ruby`, `lua`, `json`, `jsonc`, `yaml`, `yml`, `toml`, `ini`, `dotenv`, `xml`, `svg`, `markdown`, `dockerfile`, `makefile`, `graphql`, `gql`, `protobuf`, `proto`, `diff`, `patch`. Aliases include `js`, `ts`, `py`, `shell`, `sh`, `ps1`, `pwsh`,
`cmd`, `asm`, `nasm`, `masm`, `gas`, `cs`, `c#`, `kt`, `kts` and `kotlin-script`. Shell profiles share one model; naming a
profile does not install or execute that shell.

## Assets and performance

- Models and WASM are emitted as your application's static assets. Code is sent
  only to its local worker; no source-upload endpoint or CDN is required.
- The current float32 ONNX models are about **3.6 MB each, uncompressed**; exact
  per-model sizes are listed in the support tables below. The shared WASM binary
  is about **14.8 MB uncompressed** (about 3.8 MB with gzip). HTTP compression is
  optional; cache static assets normally. Models load lazily; the
  optional resource package contains all models, so select descriptors to reduce
  deployment assets.
- Inference requires a modern browser with WebAssembly SIMD, module Workers and
  Web Crypto, on HTTPS or localhost. It uses one WASM CPU thread, without requiring
  cross-origin isolation. WebGPU and a legacy-browser fallback are not implemented.
- First-use latency includes asset fetch, integrity verification and session
  initialization. Local smoke timings are not a mobile or network benchmark.

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
import "@nsh/highlighter/themes.css";
import { themes } from "@nsh/highlighter/themes";
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

The Playground offers the same independent controls: a **Theme** selector and
light/dark buttons. It retains workspace dependencies and browser inference.
Neither palette switching nor mode switching reruns the model.

To include only one preset, use `@nsh/highlighter/themes/muted.css` and select
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
import "@nsh/highlighter/theme.css";
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
import "@nsh/highlighter/theme.css";
import "./theme.css";
```

For the React/Vue shared initializer, add `import "./theme.css"` after the default
theme import in `src/highlighter.ts`. Start with
[examples/theme.css](examples/theme.css) as `src/theme.css`:

```css
/* Load after @nsh/highlighter/theme.css. These are example application colors. */
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
dependencies used for composed highlighting. Models download only when used;
[explicit language imports](#load-only-the-languages-you-need) limit which model
assets are included in your application's production build.

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
| [Dart / Flutter](packs/dart/model/README.md)                | `flutter`                                              | `dart`       |    894,872 |  3.602 MB | [95.07%](packs/dart/model/BENCHMARKS.md) — exposed 20-file regression                                                            |
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

C++ uses `cpp` (`c++` and `cxx` aliases). Existing `.h` extension mapping stays C;
pass `{ language: "cpp" }` explicitly for C++ header contents. C and C++ use
separate models and their own measured evidence.

PHP uses `{ language: "php" }`. Its descriptor includes the existing HTML/JS/CSS
dependencies for predicted-region template composition. No PHP interpreter, SDK,
Composer or server is needed. The table reports base PHP/region quality; full
composed template diagnostics are separate in the model report.

## Development and training

External training data lives outside the repository at
`~/Datasets/neural-semantic-highlighting/<model-name>/`. `NSH_DATASET_ROOT`
overrides the shared parent directory.

Release metadata uses portable paths and excludes local exporter stack traces.
Run `pnpm check:portable` to check current project files and model artifacts;
see [portable release metadata](docs/portable-release.md) for scope and verification.

See [development](docs/development.md) for package boundaries, checks, native
reference inference, datasets and checkpoint continuation. See
[browser export and verification](training/browser/README.md) for reproducible
ONNX conversion. Original training data, historical experiments and selected
PyTorch inference artifacts are preserved.

Svelte uses `{ language: "svelte" }` for original component source. Selective
`@nsh/highlighter/languages/svelte` registers the existing JS/TS and CSS/SCSS/Less
dependencies automatically; no Svelte app dependency or preprocessor is needed.
Attribute values remain whole spans, while template expressions and code/style
bodies use predicted-region composition. The table separates the small natural
base holdout from the eight visible composed development examples.

Rust uses `{ language: "rust" }` or `"rs"`; selective
`@nsh/highlighter/languages/rust` needs one model. Browser/Playground consumers
need no Rust SDK, Cargo or Python. The maintainer's existing toolchain was updated
for development; common syntax shares one entry, without edition auto-detection
or project compilation. Raw/format-string and local-role limits remain in the
[Rust report](packs/rust/model/BENCHMARKS.md).

Zig uses `{ language: "zig" }`; selective
`@nsh/highlighter/languages/zig` needs one model. It targets **Zig 0.17.1 only**,
with current SDK-checked display examples. Historical syntax/APIs, master and ZON
are outside this pack. Browser/Playground consumers need no Zig SDK, compiler,
Python provider or parser. See [Zig evaluation](packs/zig/model/BENCHMARKS.md)
for the small official-source holdout and measured limits.

Dart uses `{ language: "dart" }`; selective
`@nsh/highlighter/languages/dart` needs one model. Common Flutter widget code is
Dart source and uses this same entry. No Dart/Flutter SDK was installed for this
baseline; browser consumers require no SDK, analyzer, parser or Python provider.
Modern forms have bounded independent grammar coverage, without certifying every
SDK release or resolving imported widgets/types. See [Dart evaluation](packs/dart/model/BENCHMARKS.md)
for separate natural, focus and visible results.

Flutter also has a dedicated Playground entry, icon and eight examples. Use
`{ language: "flutter" }` or selectively import
`@nsh/highlighter/languages/flutter`. It shares the Dart descriptor and **one
Dart model asset**, so Flutter adds no separate model. Files keep `.dart`;
Flutter normalizes to `dart` in returned language and HTML `data-language`,
including `highlightElement` on `language-flutter` elements. Existing Dart theme
and CSS overrides apply. No Dart/Flutter SDK is installed or required.

The separate [Flutter application review](packs/dart/model-20261119-v1/FLUTTER.md) scores
93.95% exact-span F1 on 48 additional application files; eight visible framework
examples aggregate 95.73%. This supplements the historical Dart test in the table
and keeps application, visible and strict Golden evidence separate. The existing
weights were retained after review; no new training or duplicate model is added.

Swift uses `{ language: "swift" }` for original `.swift` source, including common
SwiftUI view/result-builder code. Selective `@nsh/highlighter/languages/swift`
emits one model asset; frontend applications need no Swift, Xcode, parser or
Python process. The Playground includes eight Swift/SwiftUI examples with the
existing Devicon icon and all preset/light/dark themes. See [Swift evaluation](packs/swift/model/BENCHMARKS.md)
and [known issues](packs/swift/model/KNOWN_ISSUES.md), including mixed literal
boundaries, dollar names and source-local role approximations.

Kotlin uses `{ language: "kotlin" }` for `.kt` and `.kts`, including common
coroutine/Flow, Compose and Gradle Kotlin-script syntax. `kt`, `kts` and
`kotlin-script` aliases share the same model and canonical `kotlin` output.
Selective `@nsh/highlighter/languages/kotlin` emits one model asset. Browser
applications require no JDK, Kotlin SDK, Gradle, Android environment, parser or
Python process. The Playground provides eight Kotlin/script examples, the pinned
Devicon icon and all existing preset/light/dark themes. See [Kotlin evaluation](packs/kotlin/model/BENCHMARKS.md)
and [known issues](packs/kotlin/model/KNOWN_ISSUES.md); Compose/Gradle examples
are syntax demonstrations rather than framework/build compatibility guarantees.

R uses `{ language: "r" }`. Selective `@nsh/highlighter/languages/r`
emits one model asset. Original .R/.r/.Rprofile source; common statistical/data, native and magrittr pipe syntax. Browser applications require no language
SDK, interpreter/compiler, package environment, parser or Python process. The
Playground adds eight examples and the pinned Devicon icon; all existing themes
and custom CSS apply. See [R evaluation](packs/r/model/BENCHMARKS.md) and
[known limits](packs/r/model/KNOWN_ISSUES.md).

Scala uses `{ language: "scala" }`. Selective `@nsh/highlighter/languages/scala`
emits one model asset. Common Scala 2/3 .scala/.sc/.sbt source, significant indentation, givens/using, extensions, enums, generics and interpolated strings. Browser applications require no language
SDK, interpreter/compiler, package environment, parser or Python process. The
Playground adds eight examples and the pinned Devicon icon; all existing themes
and custom CSS apply. See [Scala evaluation](packs/scala/model/BENCHMARKS.md) and
[known limits](packs/scala/model/KNOWN_ISSUES.md).

Ruby uses `{ language: "ruby" }`. Aliases `rb`, `rake`, `gemspec`, `gemfile` and `rakefile` normalize to `ruby`. Selective `@nsh/highlighter/languages/ruby`
emits one model asset. Common modern Ruby .rb/.rake/.gemspec and Gemfile/Rakefile syntax, classes/modules, blocks, patterns, Rails-style calls, heredocs and percent/regex literals. Browser applications require no language
SDK, interpreter/compiler, package environment, parser or Python process. The
Playground adds eight examples and the pinned Devicon icon; all existing themes
and custom CSS apply. See [Ruby evaluation](packs/ruby/model/BENCHMARKS.md) and
[known limits](packs/ruby/model/KNOWN_ISSUES.md).

Lua uses `{ language: "lua" }`. Selective `@nsh/highlighter/languages/lua`
emits one model asset. Common Lua 5.x .lua functions, closures, tables, methods, long strings/comments, 5.4 attributes and 5.5 global declarations/named varargs. Browser applications require no language
SDK, interpreter/compiler, package environment, parser or Python process. The
Playground adds eight examples and the pinned Devicon icon; all existing themes
and custom CSS apply. See [Lua evaluation](packs/lua/model/BENCHMARKS.md) and
[known limits](packs/lua/model/KNOWN_ISSUES.md).

JSON and JSONC share one JSON-family model while retaining separate document kinds
and evaluations. Use `{ language: "json" }` for strict JSON or
`{ language: "jsonc" }` for comments and common trailing-comma configurations.
Files such as `tsconfig.json` and `.vscode/launch.json` may contain JSONC despite
their extension; select `jsonc` explicitly. `.code-workspace` is a JSONC extension.
JSON5 forms, schema validation and automatic format detection are outside this pack;
highlighting itself is not a syntax validator.

Selective `@nsh/highlighter/languages/json` and `@nsh/highlighter/languages/jsonc`
share the same descriptor. Register either or both to support both kinds with
**one model asset**. Object keys use `property`, values retain their own roles,
and strings containing code/comment markers remain strings. Existing themes and
custom CSS apply. Playground has separate JSON/JSONC entries and eight examples
each. See [separate evaluations](packs/json/model/BENCHMARKS.md) and
[known limits](packs/json/model/KNOWN_ISSUES.md).

YAML uses `{ language: "yaml" }`. The `yml` alias and .yaml/.yml source share one YAML descriptor and canonical yaml output.
Selective `@nsh/highlighter/languages/yaml` emits one model asset. YAML .yaml/.yml configuration, YAML 1.2 Core scalars, mappings/sequences, quoted/block strings, anchors/aliases, tags, directives and multi-document streams.
Browser applications require no language SDK, parser or Python provider. The
Playground adds eight independent examples and the pinned Devicon icon; all theme
presets, light/dark mode and custom CSS apply. See
[YAML evaluation](packs/yaml/model/BENCHMARKS.md) and
[known limits](packs/yaml/model/KNOWN_ISSUES.md).

TOML uses `{ language: "toml" }`; selective
`@nsh/highlighter/languages/toml` emits one model asset. It covers common TOML
1.0 configuration and tested 1.1 additions, including tables, array tables,
quoted/dotted keys, inline tables, strings and date/time values. Use explicit
TOML selection for lockfiles; generic `.lock` and `.conf` extensions have no TOML
mapping. Frontend applications require no language SDK, parser or Python provider.
The Playground includes eight examples, the Devicon icon and all existing themes
and custom CSS options. See [evaluation](packs/toml/model/BENCHMARKS.md) and
[known limits](packs/toml/model/KNOWN_ISSUES.md), especially multiline strings and
quoted keys containing dots.

INI uses `{ language: "ini" }`; `cfg` and `editorconfig` are aliases for the same
model and canonical `ini` output. Selective
`@nsh/highlighter/languages/ini` emits one model asset. Common `.ini`, `.cfg` and
`.editorconfig` source covers sections, root options, repeated/empty/valueless
keys and indented continuations. Pass INI explicitly for known INI-format `.conf`
content; generic `.conf` files have no INI mapping.

INI uses whole-line `#`/`;` comments. Markers inside option values stay literal
data; application-specific inline-comment rules are outside this profile. See the
[semantic contract](packs/ini/SEMANTICS.md). The Playground includes eight examples,
including the original `.editorconfig` filename, and all existing themes/custom
CSS apply. Frontend inference needs no ConfigParser, language SDK or Python
provider. [Evaluation](packs/ini/model/BENCHMARKS.md) and
[known limits](packs/ini/model/KNOWN_ISSUES.md) retain measured continuation and
complex-value errors.

`.env` files use `{ language: "dotenv" }`; `env` and `.env` are aliases for the same
model and canonical `dotenv` output. Selective
`@nsh/highlighter/languages/dotenv` emits one model asset. Source may come from
`.env`, `.env.local`, `.env.production` or other `.env.*` files; pass its text and
an explicit language to the API.

The common profile covers variable declarations, optional `export`, plain/quoted
and multiline strings, hash comments, empty values and opaque references. Values
remain strings, including numbers and booleans. It does not load environment
variables or expand references. See the [semantic contract](packs/dotenv/SEMANTICS.md)
for dialect boundaries. The Playground includes eight examples and all existing
themes/custom CSS apply, without a Python provider, dotenv loader or language SDK.
[Evaluation](packs/dotenv/model/BENCHMARKS.md) and
[known limits](packs/dotenv/model/KNOWN_ISSUES.md) retain the small real-template
holdout and measured multiline/comment boundary errors.

XML / SVG uses `{ language: "xml" }`. XML and SVG retain distinct document kinds. languages/svg re-exports languages/xml; importing either or both shares one model asset. Select the language explicitly; filename/content auto-detection is not provided.
Selective `@nsh/highlighter/languages/xml` emits one model asset. UTF-8 XML 1.0 and SVG source, qualified tags/attributes, text, references, declarations, comments and opaque CDATA.
Browser applications require no language SDK, parser or Python provider. The
Playground adds two entries, sixteen independent examples, a Devicon XML icon and an original SVG icon; all theme
presets, light/dark mode and custom CSS apply. See
[XML / SVG evaluation](packs/xml/model/BENCHMARKS.md) and
[known limits](packs/xml/model/KNOWN_ISSUES.md).

```ts
// Default registration already includes both; choose the source kind explicitly.
await highlighter.highlight(xmlSource, { language: "xml" });
await highlighter.highlight(svgSource, { language: "svg" });
```

For a selective build, import the core factory and either or both entries:

```ts
import { createHighlighter as createMarkupHighlighter } from "@nsh/highlighter/core";
import xml from "@nsh/highlighter/languages/xml";
import svg from "@nsh/highlighter/languages/svg";
const markupHighlighter = createMarkupHighlighter({ languages: [xml, svg] });
```

SVG source is rendered as escaped code, not inserted as executable SVG markup.
CDATA and style/script/path attribute values remain opaque in this XML/SVG
baseline; it does not add embedded CSS/JavaScript or SVG path-command highlighting.

Markdown uses `{ language: "markdown" }`. markdown, md, mdown and mkd (case normalized) share one model and canonical markdown output. Source language is explicit; content detection and MDX are not supported. Default browser registration can reuse existing code models inside predicted top-level fences; selective Markdown imports require explicit registration of desired child descriptors and otherwise retain code text.
Selective `@nsh/highlighter/languages/markdown` emits one model asset. Markdown/GFM source, headings, lists/tasks, tables, links/references, nested emphasis, code, opaque HTML/front matter and predicted top-level fenced regions.
Browser applications require no language SDK, parser or Python provider. The
Playground adds eight independent examples and the pinned Devicon Markdown icon; all theme
presets, light/dark mode and custom CSS apply. See
[Markdown evaluation](packs/markdown/model/BENCHMARKS.md) and
[known limits](packs/markdown/model/KNOWN_ISSUES.md).

For a selective Markdown build with TS/JS/JSX/TSX fences:

````ts
import { createHighlighter } from "@nsh/highlighter/core";
import markdown from "@nsh/highlighter/languages/markdown";
import typescript from "@nsh/highlighter/languages/typescript";
import "@nsh/highlighter/themes.css";

const highlighter = createHighlighter({ languages: [markdown, typescript] });
const code = "# Example\n\n```tsx\nexport const App = () => <button>Open</button>;\n```";
const { html } = await highlighter.highlight(code, { language: "md" });
document.querySelector("#example")!.innerHTML = html;
````

Importing only `markdown` emits one model asset and keeps predicted code bodies
opaque. Register additional descriptors for the fence languages your application
needs; Markdown plus TypeScript emits two model assets. Default registration
already includes all supported children. Unknown/unregistered languages and
recursive Markdown fences stay code when their region is predicted. No source
language is guessed. Nested/indented code, raw HTML and front matter stay opaque.

The result displays escaped Markdown source. Headings/links/code use shared
`--nsh-heading`, `--nsh-link`, `--nsh-link-destination`, `--nsh-code`,
`--nsh-code-fence` and `--nsh-code-language` variables. Nested formatting uses
`--nsh-strong-font-weight`, `--nsh-emphasis-font-style` and
`--nsh-strikethrough-text-decoration`. All three presets and light/dark modes
include these roles. Code-fence child spans retain their own language colors.
The optimized Markdown model reaches **95.10% exact-span F1 on 20 new independent
real documents**. The same 14-file v1 regression improves from **77.24% to 95.99%**.
The 894,227-parameter backbone and semantic contract are unchanged; a train-fitted
joint decoder improves boundary/role consistency in both browser and Python.
All seven visible top-level code-body/info ranges now match. Strict edge cases
and some long fenced bodies remain weaker; detailed per-role results and the
complete previous model bundles are retained in the evaluation links above.

Base Markdown F1 measures source-role/region predictions; it does not establish
complete accuracy for composed code. See the recorded limits before relying on
long prose/fence boundaries. MDX remains a separate unsupported format.

Dockerfile uses `{ language: "dockerfile" }`; `docker` and `containerfile` are
case-normalized aliases for the same model. `Dockerfile`, `Dockerfile.production`
and `build.dockerfile` contents use the same explicit language selection. Docker
Compose remains YAML; it does not require another Dockerfile model.

```ts
import { createHighlighter } from "@nsh/highlighter/core";
import dockerfile from "@nsh/highlighter/languages/dockerfile";
import "@nsh/highlighter/themes.css";

const highlighter = createHighlighter({ languages: [dockerfile] });
const { html } = await highlighter.highlight(source, { language: "dockerfile" });
document.querySelector("#example")!.innerHTML = html;
```

The selective Dockerfile import emits **one** model asset. Shell/JSON roles are
learned within this standalone model from offline supervision; consumers need no
Docker Engine, Go, Python or parser. All presets, light/dark modes and custom
`--nsh-*` CSS apply. Register `markdown` beside `dockerfile` to reuse it in
model-predicted explicit Dockerfile fences; default registration already includes
both. See [evaluation](packs/dockerfile/model/BENCHMARKS.md) and
[known limits](packs/dockerfile/model/KNOWN_ISSUES.md).

Makefile uses `{ language: "makefile" }`; `make`, `mk`, `mak`, `gnumake` and
`gnumakefile` are case-normalized aliases for the same standalone model.
`Makefile`, `GNUmakefile` and `.mk`/`.mak` contents use explicit language selection.
CMake, NMake and complete BSD make remain separate unsupported dialects.

```ts
import { createHighlighter } from "@nsh/highlighter/core";
import makefile from "@nsh/highlighter/languages/makefile";
import "@nsh/highlighter/themes.css";

const highlighter = createHighlighter({ languages: [makefile] });
const { html } = await highlighter.highlight(source, { language: "makefile" });
document.querySelector("#example")!.innerHTML = html;
```

Selective import emits **one** model asset, with learned Make and recipe roles.
Consumers need no Make executable, language SDK, Python, parser or nested Shell
model. All presets, light/dark modes and custom `--nsh-*` CSS apply. Register
`markdown` beside `makefile` to reuse it in model-predicted explicit Makefile
fences; default registration includes both. No Makefile, recipe, expansion or
included file is executed or loaded. See [evaluation](packs/makefile/model/BENCHMARKS.md)
and [known limits](packs/makefile/model/KNOWN_ISSUES.md).
