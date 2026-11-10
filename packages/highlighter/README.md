# @nsh/highlighter

Neural code highlighting directly in the browser. Currently private and
unpublished; see the repository README for local tarball installation.

```ts
import { createHighlighter } from "@nsh/highlighter";
import "@nsh/highlighter/theme.css";

const highlighter = createHighlighter(); // Reuse this instance.
const { html } = await highlighter.highlight(source, { language: "tsx" });
container.innerHTML = html;
```

`html` is an escaped complete `<pre class="nsh"><code>` block; `value` is the token
markup alone. `highlightElement(codeElement)` reads `language-*` or `data-language`.
Use explicit languages; there is no automatic detection. Inference is asynchronous
and runs in a Web Worker. The consumer needs no Python process or server endpoint.
Call `close()` to terminate the worker when finished. Inference is client-only;
importing the module itself does not start a worker.

To select deployment assets:

```ts
import { createHighlighter } from "@nsh/highlighter/core";
import typescript from "@nsh/highlighter/languages/typescript";
const highlighter = createHighlighter({ languages: [typescript] });
```

JS/TS includes JSX/TSX. CSS includes SCSS/Less. HTML and Vue descriptors include
their JS/TS/CSS dependencies automatically. Default registration covers 19 packs;
weights are fetched lazily. Models are about 3.7 MB each, with a shared 14.8 MB
uncompressed WASM asset. Vite production bundling is verified; other bundlers are
not yet verified. HTTPS or localhost and a modern WASM/Worker browser are required.

`theme.css` provides the Default preset. For all presets:

```ts
import "@nsh/highlighter/themes.css";
import { themes } from "@nsh/highlighter/themes";
```

Set `data-nsh-preset="default"`, `"muted"` or `"contrast"` on a code block or its
ancestor. Independently set `data-nsh-theme="light"` / `"dark"` on an ancestor,
or `data-theme` on an individual `.nsh` block. Missing a preset selects Default.
For a single preset, import `@nsh/highlighter/themes/muted.css` and set its ID.
The catalog contains IDs/names/descriptions; it does not load CSS by itself.

Every preset has complete paired palettes plus optional language accents.
Switching styles or mode reuses the existing highlighted markup. Public
`--nsh-*` variables override both base and language colors; font/layout rules
can be customized with ordinary application CSS.
Models retain their measured limitations; this package does not claim perfect
classification or full highlight.js API compatibility.

Java source is available with `{ language: "java" }`, including package/module
descriptors. To ship only Java, import the descriptor from
`@nsh/highlighter/languages/java` and pass it to the configurable `./core` entry.
All three built-in theme presets cover its roles. No JDK is required by consumers.

C# source uses `{ language: "csharp" }`, with `cs` and `c#` aliases. Import
`@nsh/highlighter/languages/csharp` with the configurable `./core` entry to include
only that model. Browser consumers need no .NET SDK, Mono or source parser.

C source uses `{ language: "c" }`, or the selective descriptor
`@nsh/highlighter/languages/c`. C++ uses `{ language: "cpp" }`, with `c++` and
`cxx` aliases, or `@nsh/highlighter/languages/cpp`. They are separate models;
existing `.h` extension mapping remains C. Pass `cpp` explicitly for C++ header
contents. Consumers need no C/C++ compiler, SDK, parser or preprocessor.

PHP uses `{ language: "php" }`, including tagged source, tagless snippets and
`.phtml` templates. Selective `@nsh/highlighter/languages/php` registers existing
HTML/JS/CSS dependencies for predicted-region composition. The selective Vite
build emits four model assets, fetched lazily when needed. No PHP interpreter,
SDK, Composer or Python/server provider is required. Base PHP/region accuracy
and visible composed template accuracy are separate in the repository report.

Svelte uses `{ language: "svelte" }` for `.svelte` source. Selective
`@nsh/highlighter/languages/svelte` registers existing JS/TS and CSS/SCSS/Less
dependencies; a Vite build emits three model assets, fetched on demand. Legacy
component syntax and common Svelte 5 runes/snippets share this entry. Consumers
need no Svelte SDK/runtime, preprocessor or Python/server provider. Whole attribute
values are opaque; template expressions and script/style bodies use only predicted
regions. See [Svelte evidence](../../packs/svelte/model/BENCHMARKS.md) and
[known issues](../../packs/svelte/model/KNOWN_ISSUES.md) before treating base or
visible composed scores as general accuracy.
