# Vanilla JavaScript integration

This example uses ordinary HTML, CSS and JavaScript. Vite resolves the npm imports
and emits Worker/WASM/model assets; no React, Vue or inference server is needed.
A direct CDN/script bundle without a build step is not currently distributed.

After running `pnpm pack:browser` in the NSH repository:

1. Create a new directory and copy `index.html`, `main.js` and `style.css` here
   into it.
2. From that directory, run:

```bash
npm init -y
npm install /path/to/neural-semantic-highlighting/artifacts/browser/npm/*.tgz
npm install --save-dev vite@8.2.2
npx vite
```

Open the URL printed by Vite. For static deployment, run `npx vite build` and
serve the generated `dist` directory. The built page performs inference locally.

The full files are also included in the root README. This version includes
editable source, language selection, loading/error messages, safe plain-code
fallback and protection from obsolete results. Click Highlight after editing.
Switching the theme changes CSS only and does not trigger another inference.

`style.css` includes an example custom light/dark palette. See the
[root theme guide](../../README.md#light--dark-themes-and-custom-css) for all
supported theme attributes, CSS variables and optional system preference syncing.
