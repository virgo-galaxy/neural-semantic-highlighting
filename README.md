<p align="center">
  <a href="https://nsh.virgogalaxy.com/">
    <img src="apps/playground/public/favicon.svg" alt="Virgo NSH logo" width="96" height="96" />
  </a>
</p>

<h1 align="center">Virgo NSH</h1>

<p align="center">
  <a href="https://github.com/virgo-galaxy/virgo-nsh/actions/workflows/ci.yml">
    <img src="https://github.com/virgo-galaxy/virgo-nsh/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI status" />
  </a>
  <a href="https://www.npmjs.com/package/@virgo-nsh/highlighter">
    <img src="https://img.shields.io/npm/v/@virgo-nsh/highlighter?logo=npm&amp;cacheSeconds=300" alt="npm version" />
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license" />
  </a>
  <a href="package.json">
    <img src="https://img.shields.io/badge/node.js-24.x-339933?logo=nodedotjs&amp;logoColor=white" alt="Node.js 24.x" />
  </a>
  <a href="package.json">
    <img src="https://img.shields.io/badge/pnpm-11.25.0-F69220?logo=pnpm&amp;logoColor=white" alt="pnpm 11.25.0" />
  </a>
</p>

<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <a href="https://nsh.virgogalaxy.com/">Try the Playground</a>
</p>

Virgo NSH (Neural Semantic Highlighting) highlights source code and file formats
in the browser. ONNX inference runs in a Web Worker and returns escaped HTML and
semantic spans.

## Quick start

Install the package in a frontend project with an ESM bundler such as Vite.

```bash
npm install @virgo-nsh/highlighter
```

### Serve the models

The package ships the highlighter and themes. Serve the matching ONNX and JSON
files so the browser can load each model on first use.

For versions `0.1.0` and `0.1.1`, download the [model source snapshot](https://github.com/virgo-galaxy/virgo-nsh/archive/7109bac49340b94ad5350778e32ee0d4196c5698.tar.gz).
From the unpacked snapshot, run these commands with Node.js 24 and pnpm 11.

```bash
pnpm install --frozen-lockfile
pnpm build:packages
node scripts/export-model-assets.mjs --models typescript,css
```

Copy the contents of `artifacts/browser/models/` into your app's `public/models/`
directory, keeping `v1/` intact. These two model families cover JS, TS, JSX, TSX,
CSS, SCSS and Less. For other versions, use the snapshot linked in that version's
npm README. See [model delivery](docs/model-delivery.md) for separate hosting,
signed URLs and model selection.

### Highlight code

Add this to `index.html` in a plain Vite app.

```html
<div id="example">
  <pre class="nsh"><code></code></pre>
</div>
<script type="module" src="/main.js"></script>
```

Create `main.js` next to `index.html`.

```js
import { createHighlighter } from "@virgo-nsh/highlighter";
import "@virgo-nsh/highlighter/theme.css";

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

Run `npx vite` and open the URL it prints. Use HTTPS or localhost in a browser
with module Workers, WebAssembly SIMD and Web Crypto. Reuse one highlighter
across code blocks and call `close()` when the app is done with it.

## React, Vue and vanilla JavaScript

Use the same package and model setup in each framework.

- [React](examples/react/README.md) includes a reusable `CodeBlock.tsx`.
- [Vue](examples/vue/README.md) includes a reusable `CodeBlock.vue`.
- [Vanilla JavaScript](examples/vanilla/README.md) includes a Vite example and
  `highlightElement` for an existing code block.

Use [`observeElement()`](packages/highlighter/README.npm.md#highlight-on-scroll)
to highlight existing code blocks as they approach the viewport.

## Themes

The default stylesheet includes light and dark palettes. Set
`data-nsh-theme="dark"` on a parent element to switch modes. Load
`@virgo-nsh/highlighter/themes.css` for all three presets.

[Theme and custom CSS guide](docs/themes.md)

## Supported languages and measured quality

NSH has **40 model packs** covering code languages and file formats. Some
formats share weights, including JSON/JSONC and XML/SVG. Models use **512 UTF-8
bytes per inference window** and process longer documents across multiple windows.

[Supported content, model sizes and benchmark results](docs/model-benchmarks.md)

## Development

Use Node.js 24 and pnpm 11.25.0 to run the Playground from this checkout.

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Open <http://127.0.0.1:3000/>. See the [contribution guide](CONTRIBUTING.md) for
checks and pull requests, or the [development guide](docs/development.md) for
workspace layout, training and evaluation.

## License

Project-authored code and documentation are covered by the [MIT License](LICENSE).
Model weights and third-party materials have their own applicable terms.
