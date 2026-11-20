# Model delivery

The selected weights and inference algorithms stay unchanged. Delivery separates
the highlighter from the optional local resource package:

| Package / entry                    | Purpose                                                          |
| ---------------------------------- | ---------------------------------------------------------------- |
| `@nsh/highlighter` or `/core`      | Highlighter API, composition, renderer and themes; no ONNX files |
| `@nsh/browser`                     | One shared browser Worker / WASM runtime                         |
| `@nsh/models/languages/<model-id>` | Explicit local model descriptor and its asset                    |
| `@nsh/highlighter/bundled`         | Explicitly include every local model; requires `@nsh/models`     |
| `@nsh/highlighter/languages/*`     | Compatibility forwards to the optional resource package          |

These packages remain private and unpublished. Installing `@nsh/models` locally
installs its complete resource archive. Importing only selected subpaths limits
the ONNX files in the application's deployment; these are different sizes.

## Local application assets

```ts
import { createHighlighter } from "@nsh/highlighter";
import "@nsh/highlighter/theme.css";
import css from "@nsh/models/languages/css";
import typescript from "@nsh/models/languages/typescript";

const highlighter = createHighlighter({ languages: [typescript, css] });
await highlighter.highlight(source, { language: "tsx" });
await highlighter.highlight(styles, { language: "scss" });
```

The standalone [example](../examples/selective/main.js) exercises TSX and SCSS.
The independently installed Vite build emits exactly two selected ONNX models
(7,213,247 bytes total), one shared WASM and the normal JS/CSS assets. Browser
checks preserve the original source and produce semantic spans for both inputs.

HTML, Vue, Svelte and PHP descriptors collect their existing script/style/markup
dependencies automatically. Markdown can reuse other explicitly registered fence
languages. A shared model such as TypeScript or CSS is collected once.

## Reproduce package and production-build checks

Build the workspace packages first. The packer rewrites workspace dependency
versions in temporary staging manifests and calls `npm pack` locally; no package
is published and no repository manifest is modified by packing.

```bash
pnpm build:packages
node scripts/pack-browser.mjs
node scripts/check-model-delivery.mjs
```

The consumer check installs actual archives into temporary projects outside the
checkout, so imports cannot resolve through workspace links. It checks selected
weight hashes, ONNX counts and shared WASM counts. `--offline` and
`--seed-node-modules <directory>` support reusing existing third-party packages
without registry access. The optional seed excludes all `@nsh` packages.

[Recorded local verification](model-delivery-local-verification.json) includes
archive sizes and the two independent builds. Archive sizes use npm's packing
compression; per-model sizes in the main README are original ONNX file sizes.

The resource build produces `packages/models/dist/assets/manifest.json` and
`v1/<model-id>/<sha256>.onnx` files with pinned metadata sidecars. This directory
can be copied as static resources. Remote highlighter configuration is the next
delivery stage.
