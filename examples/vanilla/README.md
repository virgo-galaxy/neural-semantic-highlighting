# Vanilla JavaScript integration

This example uses HTML, CSS and JavaScript with Vite to resolve npm imports and
build the browser Worker and WASM assets. Copy [index.html](index.html),
[main.js](main.js) and [style.css](style.css) to a new directory. In that directory:

```bash
npm init -y
npm install --save-dev vite@8.2.2
```

Install the [npm package](../../docs/model-delivery.md#install-from-npm).
Replace the imports and initializer at the top of `main.js` with this block.

```js
import "neural-semantic-highlighting/theme.css";
import "./style.css";

import { createHighlighter } from "neural-semantic-highlighting";

const highlighter = createHighlighter({
  modelBaseUrl: "/models/",
  languages: ["typescript", "javascript", "css"],
});
```

Serve the [exported model directory](../../docs/model-delivery.md#export-the-deployable-directory)
at `/models/`, or use its full URL. Start the example and open the URL it prints.

```bash
npx vite
```

For static deployment, run `npx vite build` and serve `dist/`. Serve the
TypeScript and CSS model files at the configured URL.

Click **Highlight** after editing to render the source. The example keeps plain
code visible while loading or after an error and skips obsolete results.
Switching the theme changes CSS only and does not trigger another inference.

For a page that already has code blocks, render one directly with the same
initializer and `highlightElement`:

```html
<pre><code id="example" class="language-typescript">const answer = 42;</code></pre>
```

```js
const element = document.querySelector("#example");
if (element) {
  try {
    await highlighter.highlightElement(element);
  } catch (error) {
    console.error("Unable to highlight the example", error);
  }
}
```

`style.css` includes an example custom light/dark palette. See the
[root theme guide](../../README.md#light--dark-themes-and-custom-css) for all
supported theme attributes, CSS variables and optional system preference syncing.
