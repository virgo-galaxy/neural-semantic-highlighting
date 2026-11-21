# Neural Semantic Highlighting

Highlight source code and file formats in the browser. A Web Worker runs
inference using ONNX models. The highlighter returns escaped HTML and semantic
spans.

## Install a local candidate

In a frontend project with an ESM bundler such as Vite, install the archive from
the NSH checkout:

```bash
npm install /path/to/neural-semantic-highlighting-0.1.0.tgz
```

## Highlight a code block

```js
import { createHighlighter } from "neural-semantic-highlighting";
import "neural-semantic-highlighting/theme.css";

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
app no longer needs it. Call inference on the client. The browser needs module
Workers, WebAssembly SIMD and Web Crypto. Serve the app over HTTPS or localhost.

## Serve model assets

From a matching NSH checkout with the workspace packages built, export the
models for the content types your app uses:

```bash
node scripts/export-model-assets.mjs --models typescript,css
```

The export goes to `artifacts/browser/models/`. Keep its `v1/` directory
structure intact. Set `modelBaseUrl` to a same-site path such as `/models/` or
an HTTPS URL on a separate host that allows cross-origin reads. For private
models, use `resolveAssetUrl` to supply download URLs such as signed URLs.

The npm archive includes the API, HTML renderer, CSS themes and inference
runtime. It contains zero ONNX weights. The browser downloads each required
model and its metadata from your host when first used. Omit `languages` to
offer the full catalog when hosting all models. Use the `/catalog` package
entry to list content types or the `/themes.css` entry to load all theme presets.

## License

The project's code and documentation are licensed under MIT. The archive
includes the `LICENSE` file and the original ONNX Runtime license notice.
