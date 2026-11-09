# Neural Semantic Highlighting

Neural code highlighting for frontend applications. Import a highlighter, pass
source code and its language, and render the returned HTML. Inference runs locally
in a browser Web Worker using the existing models; consumers need no Python
process, language SDK or highlighting server.

**Distribution status:** this repository and all packages are still private.
`@nsh/highlighter` is the current package name in this workspace, **not a package
already published on npm**. Local tarball installation works today. Publication
and repository visibility are separate release decisions.

[Install](#try-it-now) · [Simple usage](#simple-integration-react-vue-and-vanilla-javascript) ·
[Complete examples](#complete-integration-examples) ·
[Themes and custom CSS](#light--dark-themes-and-custom-css)

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

This installs the highlighter and its three internal dependencies from local
archives. Use an ESM frontend bundler; Vite production builds have been verified.
Other bundlers have not yet been verified. No alias into this repository, Python
setup, special Vite bridge or manual model URL configuration is required.

## Highlight code

```ts
import { createHighlighter } from "@nsh/highlighter";
import "@nsh/highlighter/theme.css";

// Create once and reuse: models are fetched on first use, then kept in the worker.
const highlighter = createHighlighter();
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
import "@nsh/highlighter/theme.css";

const highlighter = createHighlighter();
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

// One worker and model cache for the whole client application.
export const highlighter = createHighlighter();
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

const highlighter = createHighlighter();
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

## Load only the languages you need

The default entry registers all current models, but downloads weights only when
used. For a smaller production asset set, select models explicitly:

```ts
import { createHighlighter } from "@nsh/highlighter/core";
import typescript from "@nsh/highlighter/languages/typescript";
import css from "@nsh/highlighter/languages/css";
import "@nsh/highlighter/theme.css";

const highlighter = createHighlighter({ languages: [typescript, css] });
await highlighter.highlight(source, { language: "tsx" });
```

The TypeScript descriptor covers JS, TS, JSX and TSX. CSS covers CSS, SCSS and
Less. HTML and Vue descriptors automatically include the existing script/style
models they need. Composition uses neurally predicted embedded regions, not a
source parser. Tailwind classes remain string values.

Common language IDs: `javascript`, `typescript`, `jsx`, `tsx`, `go`, `css`, `scss`,
`less`, `html`, `vue`, `python`, `bash`, `zsh`, `csh`, `tcsh`, `sql`, `powershell`,
`bat`, `assembly`, `java`, `csharp`. Aliases include `js`, `ts`, `py`, `shell`, `sh`, `ps1`, `pwsh`,
`cmd`, `asm`, `nasm`, `masm`, `gas`, `cs` and `c#`. Shell profiles share one model; naming a
profile does not install or execute that shell.

## Assets and performance

- Models and WASM are emitted as your application's static assets. Code is sent
  only to its local worker; no source-upload endpoint or CDN is required.
- The current float32 models are about **3.7 MB each**. The shared WASM binary is
  about **14.8 MB uncompressed** (about 3.9 MB with gzip). Serve compressed assets
  and cache them normally. Registration is lazy; the default package still
  contains all models, so select descriptors to reduce deployment assets.
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

## Supported languages and measured quality

There are **16 model packs**, with browser inference and Playground examples.
The browser conversion preserves the selected weights without retraining or
quantization. [Browser verification](docs/browser-runtime.md) records conversion
checks and the exact-output comparison across 99 examples/edge cases, including
Java, C# and C. Independent local-package verification also covers its public imports. This is
runtime parity evidence, not a new accuracy evaluation.

The table reports **exact-span F1**: token start, end and semantic type must match.
It is not character accuracy or the percentage of perfect files. Different test
sets and sample sizes are not directly comparable. Reports retain known limits.

| Name                                                        | Supported source / file extensions                                                                                                                                  | Measured test exact-span F1                                                                                 | Current state / measured limits                                                                                                       |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| [JavaScript / TypeScript](packs/typescript/model/README.md) | JS/TS modules and declarations, JSX/TSX including React component source; `.js`, `.mjs`, `.cjs`, `.jsx`, `.ts`, `.mts`, `.cts`, `.tsx`, `.d.ts`, `.d.mts`, `.d.cts` | [99.31%](packs/typescript/model/BENCHMARKS.md) — archived combined whole-document test                      | Browser + local; [RegExp, comment and long-string boundaries](packs/typescript/model/KNOWN_ISSUES.md) remain limited                  |
| [Go](packs/go/model/README.md)                              | Go source; `.go`                                                                                                                                                    | [99.03%](packs/go/model/README.md#selected-candidate) — natural test                                        | Browser + local; [long raw strings and cross-file names](packs/go/model/KNOWN_ISSUES.md) remain limited                               |
| [CSS / SCSS / Less](packs/css/model/README.md)              | Stylesheets and preprocessor source; `.css`, `.scss`, `.less`                                                                                                       | [CSS 99.04%; SCSS 99.40%; Less 99.42%](packs/css/model/BENCHMARKS.md) — natural test, per language          | Browser + local; [individual grid/token and boundary errors](packs/css/model/KNOWN_ISSUES.md) remain                                  |
| [HTML](packs/html/model/README.md)                          | Modern HTML; `.html`, `.htm`; JS/CSS composition inside predicted `<script>` / `<style>` bodies                                                                     | [Markup 96.37%; composed 96.53%](packs/html/model/BENCHMARKS.md) — natural test, separate scopes            | Browser + local; [comments and embedded-region boundaries](packs/html/model/KNOWN_ISSUES.md) remain limited                           |
| [Vue](packs/vue/model/README.md)                            | Vue 2 / Vue 3 / Vue 3.2 SFCs; `.vue`; existing script/style models reused                                                                                           | [97.12%](packs/vue/model/BENCHMARKS.md) — natural composed test; profile results are separate in the report | Browser + local; [SFC region boundaries and sparse syntax coverage](packs/vue/model/KNOWN_ISSUES.md) remain limited                   |
| [Python](packs/python/model/README.md)                      | Python 3 source and stubs; `.py`, `.pyw`, `.pyi`                                                                                                                    | [87.52%](packs/python/model/BENCHMARKS.md) — natural test                                                   | Usable baseline; [name roles and long docstrings](packs/python/model/KNOWN_ISSUES.md) remain weaker                                   |
| [Shell](packs/bash/model/README.md)                         | POSIX sh, Bash, Zsh, Csh/Tcsh; `.sh`, `.bash`, `.zsh`, `.csh`, `.tcsh`; Git Bash shares Bash syntax                                                                 | [84.78% overall; Bash 93.20%](packs/bash/model/BENCHMARKS.md) — known natural-test comparison               | Usable baseline, Bash prioritized; [complex Zsh and Here Document endings](packs/bash/model/KNOWN_ISSUES.md) remain weaker            |
| [Perl](packs/perl/model/README.md)                          | Perl 5 scripts, modules and tests; `.pl`, `.pm`, `.t`, `.perl`                                                                                                      | [83.60%](packs/perl/model/BENCHMARKS.md) — natural test                                                     | Usable baseline; [mixed Here Documents and role/modifier boundaries](packs/perl/model/KNOWN_ISSUES.md) remain weaker                  |
| [AWK](packs/awk/model/README.md)                            | Common POSIX-style / GNU AWK; `.awk`, `.gawk`                                                                                                                       | [96.89%](packs/awk/model/BENCHMARKS.md) — natural test                                                      | Browser + local; [regex span boundaries and advanced GNU calls](packs/awk/model/KNOWN_ISSUES.md) remain limited                       |
| [SQL](packs/sql/model/README.md)                            | PostgreSQL/psql, MySQL, Oracle/SQL*Plus; `.sql`, `.psql`, `.pgsql`, `.plsql`                                                                                        | [88.41%](packs/sql/model/BENCHMARKS.md) — natural test; per-profile results in report                       | Usable baseline; [special strings, mixed client commands and procedural names](packs/sql/model/KNOWN_ISSUES.md) remain weaker         |
| [PowerShell](packs/powershell/model/README.md)              | Common Windows/modern PowerShell scripts, modules and data; `.ps1`, `.psm1`, `.psd1`                                                                                | [90.67%](packs/powershell/model/BENCHMARKS.md) — natural test                                               | Usable baseline; [string boundaries, long bodies and name flags](packs/powershell/model/KNOWN_ISSUES.md) remain limited               |
| [BAT / CMD](packs/bat/model/README.md)                      | Common Windows cmd.exe batch scripts; `.bat`, `.cmd`                                                                                                                | [74.29%](packs/bat/model/BENCHMARKS.md) — natural test, 3 scripts                                           | Initial baseline; [conditional tails, quoted variables and argument roles](packs/bat/model/KNOWN_ISSUES.md) remain weaker             |
| [Assembly](packs/assembly/model/README.md)                  | Common NASM/Intel, GNU/AT&T, MASM, AArch64; `.asm`, `.ASM`, `.nasm`, `.masm`, `.s`, `.S`, assembly `.inc`                                                           | [98.63%](packs/assembly/model/BENCHMARKS.md) — natural test, 5 files; per-profile results in report         | Browser + local; [macro parameters, names, modifiers and comment boundaries](packs/assembly/model/KNOWN_ISSUES.md) remain limited     |
| [Java](packs/java/model/README.md)                          | Java source and package/module descriptors; `.java`; common Java 8–22 and non-preview modern syntax through JDK 22                                                  | [92.60%](packs/java/model/BENCHMARKS.md) — natural test, 29 files                                           | Browser + local; [local name roles, guarded patterns and module paths](packs/java/model/KNOWN_ISSUES.md) remain limited               |
| [C#](packs/csharp/model/README.md)                          | C# source; `.cs`; classes, structs, records, attributes, LINQ, async and modern strings accepted by the pinned grammar                                              | [94.64%](packs/csharp/model/BENCHMARKS.md) — natural test, 24 files                                         | Browser + local; [complex property patterns, record names and distant local roles](packs/csharp/model/KNOWN_ISSUES.md) remain limited |
| [C](packs/c/model/README.md)                                | C source and explicitly C headers; `.c`, `.h`; common C11/C17 and accepted modern/GNU forms, including pointers, structs, macros and callbacks                      | [93.90%](packs/c/model/BENCHMARKS.md) — natural test, 18 files                                              | Browser + local; [macro parameters, local roles and string/literal boundaries](packs/c/model/KNOWN_ISSUES.md) remain limited          |

## Development and training

See [development](docs/development.md) for package boundaries, checks, native
reference inference, datasets and checkpoint continuation. See
[browser export and verification](training/browser/README.md) for reproducible
ONNX conversion. Original training data, historical experiments and selected
PyTorch inference artifacts are preserved.
