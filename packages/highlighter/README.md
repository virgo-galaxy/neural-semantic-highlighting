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
their JS/TS/CSS dependencies automatically. Default registration covers 13 packs;
weights are fetched lazily. Models are about 3.7 MB each, with a shared 14.8 MB
uncompressed WASM asset. Vite production bundling is verified; other bundlers are
not yet verified. HTTPS or localhost and a modern WASM/Worker browser are required.

The bundled theme supports `data-theme="dark"` and `--nsh-*` CSS overrides.
Models retain their measured limitations; this package does not claim perfect
classification or full highlight.js API compatibility.
