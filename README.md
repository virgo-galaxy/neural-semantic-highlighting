# Neural Semantic Highlighting

Neural code highlighting for frontend applications. Import a highlighter, pass
source code and its language, and render the returned HTML. Inference runs locally
in a browser Web Worker using the existing models; consumers need no Python
process, language SDK or highlighting server.

**Distribution status:** this repository and all packages are still private.
`@nsh/highlighter` is the current package name in this workspace, **not a package
already published on npm**. Local tarball installation works today. Publication
and repository visibility are separate release decisions.

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

## React and Vue

A complete React component is in [examples/react/CodeBlock.tsx](examples/react/CodeBlock.tsx):

```tsx
import { CodeBlock } from "./CodeBlock";

<CodeBlock code={source} language="tsx" />;
```

It reuses one highlighter, preserves readable code while loading, handles errors
and ignores results from an older render. Import the theme once in your app.

In a Vue 3 component, the same API can be used with `v-html`:

```vue
<script setup lang="ts">
import { createHighlighter } from "@nsh/highlighter";
import { onBeforeUnmount, ref, watch } from "vue";
import "@nsh/highlighter/theme.css";

const props = defineProps<{ code: string; language: string }>();
const highlighter = createHighlighter();
const markup = ref("");
const error = ref("");
watch(
  () => [props.code, props.language],
  async (_, __, onCleanup) => {
    let active = true;
    onCleanup(() => {
      active = false;
    });
    markup.value = "";
    error.value = "";
    try {
      const result = await highlighter.highlight(props.code, { language: props.language });
      if (active) markup.value = result.value;
    } catch (reason) {
      if (active) error.value = String(reason);
    }
  },
  { immediate: true },
);
onBeforeUnmount(() => highlighter.close());
</script>

<template>
  <pre
    class="nsh"
    :data-language="language"
  ><code v-if="markup" v-html="markup"></code><code v-else>{{ code }}</code></pre>
  <p v-if="error" role="alert">{{ error }}</p>
</template>
```

The full Vue Playground is another working consumer. No framework dependency is
included in the highlighter package.

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
`bat`, `assembly`. Aliases include `js`, `ts`, `py`, `shell`, `sh`, `ps1`, `pwsh`,
`cmd`, `asm`, `nasm`, `masm` and `gas`. Shell profiles share one model; naming a
profile does not install or execute that shell.

## Assets, performance and themes

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
- Use `data-theme="dark"` on `.nsh` or `data-nsh-theme="dark"` on an ancestor for
  dark mode. Customize `--nsh-*` CSS variables to match your application.

## Supported languages and measured quality

There are **13 model packs**, with browser inference and Playground examples.
The browser conversion preserves the selected weights without retraining or
quantization. [Browser verification](docs/browser-runtime.md) records conversion
checks and the exact-output comparison across 76 examples/edge cases. This is
runtime parity evidence, not a new accuracy evaluation.

The table reports **exact-span F1**: token start, end and semantic type must match.
It is not character accuracy or the percentage of perfect files. Different test
sets and sample sizes are not directly comparable. Reports retain known limits.

| Name                                                        | Supported source / file extensions                                                                                                                                  | Measured test exact-span F1                                                                                 | Current state / measured limits                                                                                                   |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| [JavaScript / TypeScript](packs/typescript/model/README.md) | JS/TS modules and declarations, JSX/TSX including React component source; `.js`, `.mjs`, `.cjs`, `.jsx`, `.ts`, `.mts`, `.cts`, `.tsx`, `.d.ts`, `.d.mts`, `.d.cts` | [99.31%](packs/typescript/model/BENCHMARKS.md) — archived combined whole-document test                      | Browser + local; [RegExp, comment and long-string boundaries](packs/typescript/model/KNOWN_ISSUES.md) remain limited              |
| [Go](packs/go/model/README.md)                              | Go source; `.go`                                                                                                                                                    | [99.03%](packs/go/model/README.md#selected-candidate) — natural test                                        | Browser + local; [long raw strings and cross-file names](packs/go/model/KNOWN_ISSUES.md) remain limited                           |
| [CSS / SCSS / Less](packs/css/model/README.md)              | Stylesheets and preprocessor source; `.css`, `.scss`, `.less`                                                                                                       | [CSS 99.04%; SCSS 99.40%; Less 99.42%](packs/css/model/BENCHMARKS.md) — natural test, per language          | Browser + local; [individual grid/token and boundary errors](packs/css/model/KNOWN_ISSUES.md) remain                              |
| [HTML](packs/html/model/README.md)                          | Modern HTML; `.html`, `.htm`; JS/CSS composition inside predicted `<script>` / `<style>` bodies                                                                     | [Markup 96.37%; composed 96.53%](packs/html/model/BENCHMARKS.md) — natural test, separate scopes            | Browser + local; [comments and embedded-region boundaries](packs/html/model/KNOWN_ISSUES.md) remain limited                       |
| [Vue](packs/vue/model/README.md)                            | Vue 2 / Vue 3 / Vue 3.2 SFCs; `.vue`; existing script/style models reused                                                                                           | [97.12%](packs/vue/model/BENCHMARKS.md) — natural composed test; profile results are separate in the report | Browser + local; [SFC region boundaries and sparse syntax coverage](packs/vue/model/KNOWN_ISSUES.md) remain limited               |
| [Python](packs/python/model/README.md)                      | Python 3 source and stubs; `.py`, `.pyw`, `.pyi`                                                                                                                    | [87.52%](packs/python/model/BENCHMARKS.md) — natural test                                                   | Usable baseline; [name roles and long docstrings](packs/python/model/KNOWN_ISSUES.md) remain weaker                               |
| [Shell](packs/bash/model/README.md)                         | POSIX sh, Bash, Zsh, Csh/Tcsh; `.sh`, `.bash`, `.zsh`, `.csh`, `.tcsh`; Git Bash shares Bash syntax                                                                 | [84.78% overall; Bash 93.20%](packs/bash/model/BENCHMARKS.md) — known natural-test comparison               | Usable baseline, Bash prioritized; [complex Zsh and Here Document endings](packs/bash/model/KNOWN_ISSUES.md) remain weaker        |
| [Perl](packs/perl/model/README.md)                          | Perl 5 scripts, modules and tests; `.pl`, `.pm`, `.t`, `.perl`                                                                                                      | [83.60%](packs/perl/model/BENCHMARKS.md) — natural test                                                     | Usable baseline; [mixed Here Documents and role/modifier boundaries](packs/perl/model/KNOWN_ISSUES.md) remain weaker              |
| [AWK](packs/awk/model/README.md)                            | Common POSIX-style / GNU AWK; `.awk`, `.gawk`                                                                                                                       | [96.89%](packs/awk/model/BENCHMARKS.md) — natural test                                                      | Browser + local; [regex span boundaries and advanced GNU calls](packs/awk/model/KNOWN_ISSUES.md) remain limited                   |
| [SQL](packs/sql/model/README.md)                            | PostgreSQL/psql, MySQL, Oracle/SQL*Plus; `.sql`, `.psql`, `.pgsql`, `.plsql`                                                                                        | [88.41%](packs/sql/model/BENCHMARKS.md) — natural test; per-profile results in report                       | Usable baseline; [special strings, mixed client commands and procedural names](packs/sql/model/KNOWN_ISSUES.md) remain weaker     |
| [PowerShell](packs/powershell/model/README.md)              | Common Windows/modern PowerShell scripts, modules and data; `.ps1`, `.psm1`, `.psd1`                                                                                | [90.67%](packs/powershell/model/BENCHMARKS.md) — natural test                                               | Usable baseline; [string boundaries, long bodies and name flags](packs/powershell/model/KNOWN_ISSUES.md) remain limited           |
| [BAT / CMD](packs/bat/model/README.md)                      | Common Windows cmd.exe batch scripts; `.bat`, `.cmd`                                                                                                                | [74.29%](packs/bat/model/BENCHMARKS.md) — natural test, 3 scripts                                           | Initial baseline; [conditional tails, quoted variables and argument roles](packs/bat/model/KNOWN_ISSUES.md) remain weaker         |
| [Assembly](packs/assembly/model/README.md)                  | Common NASM/Intel, GNU/AT&T, MASM, AArch64; `.asm`, `.ASM`, `.nasm`, `.masm`, `.s`, `.S`, assembly `.inc`                                                           | [98.63%](packs/assembly/model/BENCHMARKS.md) — natural test, 5 files; per-profile results in report         | Browser + local; [macro parameters, names, modifiers and comment boundaries](packs/assembly/model/KNOWN_ISSUES.md) remain limited |

## Development and training

See [development](docs/development.md) for package boundaries, checks, native
reference inference, datasets and checkpoint continuation. See
[browser export and verification](training/browser/README.md) for reproducible
ONNX conversion. Original training data, historical experiments and selected
PyTorch inference artifacts are preserved.
