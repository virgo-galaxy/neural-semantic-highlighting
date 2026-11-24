# Virgo NSH

Neural semantic highlighting for source code and file formats. NSH runs ONNX
inference in a browser Web Worker and returns escaped HTML and semantic spans.

[Try the live Playground](https://nsh.virgogalaxy.com/) ·
[React, Vue and vanilla JS](https://github.com/virgo-galaxy/virgo-nsh#react-vue-and-vanilla-javascript) ·
[简体中文](https://github.com/virgo-galaxy/virgo-nsh/blob/main/README.zh-CN.md)

## Install

In a frontend project with an ESM bundler such as Vite:

```bash
npm install @virgo-nsh/highlighter
```

## Serve model assets

The npm package includes the API, HTML renderer, CSS themes and browser runtime.
Serve the ONNX models and their JSON metadata from your app or a static host.
The browser downloads the files on first use and runs inference locally.

For version 0.1.0, download and unpack the
[matching model source snapshot](https://github.com/virgo-galaxy/virgo-nsh/archive/7109bac49340b94ad5350778e32ee0d4196c5698.tar.gz).
From its root, export the model families you need with Node.js 24 and pnpm 11:

```bash
pnpm install --frozen-lockfile
pnpm build:packages
node scripts/export-model-assets.mjs --models typescript,css
```

For a Vite app, copy the contents of `artifacts/browser/models/` to
`public/models/` and keep the `v1/` directory intact. Set `modelBaseUrl` to
`/models/`. For a separate host, set it to the HTTPS directory that contains
`v1/` and allow cross-origin reads. Use `resolveAssetUrl` for signed URLs.
See the [model delivery guide](https://github.com/virgo-galaxy/virgo-nsh/blob/main/docs/model-delivery.md).

## Highlight a code block

Add `<div id="example"></div>` to the page and use this in your client entry:

```js
import { createHighlighter } from "@virgo-nsh/highlighter";
import "@virgo-nsh/highlighter/theme.css";

const highlighter = createHighlighter({
  modelBaseUrl: "/models/",
  languages: ["tsx", "scss"],
});

const { html } = await highlighter.highlight("const App = () => <button>Hello</button>;", {
  language: "tsx",
});
document.querySelector("#example").innerHTML = html;
```

Reuse the highlighter across code blocks and call `highlighter.close()` when the
app is done with it. Serve the app over HTTPS or localhost in a browser with
module Workers, WebAssembly SIMD and Web Crypto.

Use `@virgo-nsh/highlighter/catalog` to list content types. Load all presets with
`@virgo-nsh/highlighter/themes.css` and see the
[theme guide](https://github.com/virgo-galaxy/virgo-nsh/blob/main/docs/themes.md)
for light and dark modes and custom CSS.

## License

The project's code and documentation are licensed under MIT. The package
includes the `LICENSE` file and the original ONNX Runtime license notice.
