# Model delivery

Choose where the browser will download model files. Both modes use the same
highlighter API, CSS themes and shared browser Worker/WASM runtime.

| Mode           | Install                          | Production deployment                                     |
| -------------- | -------------------------------- | --------------------------------------------------------- |
| Website assets | Highlighter and `@nsh/models`    | The app contains the ONNX files selected by its imports   |
| Remote host    | Highlighter and its dependencies | The app contains zero ONNX files. Serve models separately |

Vite production builds have been verified. Run inference on the client in a
modern browser with WebAssembly SIMD, module Workers and Web Crypto. Serve the
app over HTTPS or localhost. Vite resolves the package imports and emits the
Worker and WASM assets.

## Install from local archives

The `@nsh` packages are unpublished. Build the `.tgz` files in the NSH checkout
with Node.js 24 and pnpm 11:

```bash
pnpm install
pnpm pack:browser
```

For maintainers preparing a release candidate, follow the
[clean build and archive checks](npm-release.md#build-and-verify-a-candidate).

Run the following in your **own frontend project**, with an existing
`package.json`. Set `NSH_ARCHIVES` to the actual archive directory. These
commands assume there is one archive per package in that directory.

```bash
NSH_ARCHIVES="/absolute/path/to/neural-semantic-highlighting/artifacts/browser/npm"
npm install "$NSH_ARCHIVES"/nsh-core-*.tgz "$NSH_ARCHIVES"/nsh-html-*.tgz \
  "$NSH_ARCHIVES"/nsh-browser-*.tgz "$NSH_ARCHIVES"/nsh-highlighter-*.tgz
```

For **Website assets** only, also install the resource archive from the same build:

```bash
npm install "$NSH_ARCHIVES"/nsh-models-*.tgz
```

The resource archive contains all 40 selected models. Its install size is the
same regardless of which descriptors you use. Your production build includes
only the models reachable from your imports and any composition dependencies.
For example, TSX and SCSS together emit about **7.21 MB of ONNX files** before
HTTP compression, plus one shared WASM and the application's JS/CSS. The browser
requests each model as it is used.

Once installed, use the [React](../examples/react/README.md),
[Vue 3](../examples/vue/README.md) or [vanilla JavaScript](../examples/vanilla/README.md)
guide. The rendering code stays the same for both modes. Change the highlighter
initializer to select a model source.

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

`@nsh/highlighter/bundled` is the all-model entry for apps such as the Playground.
Use individual `@nsh/models/languages/*` imports to limit the app's deployment
assets. Existing `@nsh/highlighter/languages/*` paths forward to the optional
resource package.

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

## Remote assets: static server or MinIO

The frontend installs only `@nsh/highlighter` and its normal dependencies; it
does not need the optional `@nsh/models` package. The same API accepts a resource
root and optional content IDs/aliases instead of local descriptors:

```ts
import { createHighlighter } from "@nsh/highlighter";
import "@nsh/highlighter/theme.css";

const highlighter = createHighlighter({
  modelBaseUrl: "https://storage.example.com/highlighting/",
  // Omit languages to offer all currently supported content types.
  languages: ["tsx", "scss", "vue"],
});
const { html } = await highlighter.highlight(source, { language: "tsx" });
```

`modelBaseUrl` can be an absolute HTTP(S) URL or an application-relative URL such
as `/models/`. It identifies the directory containing `v1/`; a trailing slash is
optional. For MinIO, include the bucket and any prefix in that URL.
Remote selection accepts the existing names and aliases. Local selection accepts
the optional resource package's descriptors; combining those two forms is rejected.
For example, `https://storage.example.com/model-bucket/highlighting/` points to
`highlighting/` inside `model-bucket`. The browser appends the pinned `v1/...`
paths to that base. With an HTTPS app, use an HTTPS resource host.

The highlighter bundles a small catalog pinning model and metadata hashes. On
first use, the browser fetches that model's metadata and then its ONNX directly
from the resource host. Both are hash-checked before use. Creating an instance,
listing languages and highlighting empty input download no model resources.
Composition registers required children, but their resources load only when
inference reaches an embedded region. Loaded metadata, URLs and inference
sessions are reused; failed requests can be retried. Calling `close()` rejects
pending work and aborts metadata downloads. [Model caching](model-cache.md)
documents hash-keyed persistent storage, session limits, download timeouts and
typed errors.

The frontend's source code remains in its local Worker. No highlighting endpoint,
Python provider, S3 client or custom compression/decompression code is involved.
For a different resource origin, configure MinIO/the static host's CORS policy to
allow browser `GET` requests from the exact app origin for both `.onnx` and `.json`
objects. Include the app's port for localhost development. HTTP compression is
optional. Shared WASM ships with `@nsh/browser` as an application asset.

### Export the deployable directory

After `pnpm pack:browser`, run this in the NSH checkout:

```bash
node scripts/export-model-assets.mjs
# Optional subset; required child models are included automatically:
node scripts/export-model-assets.mjs --models typescript,css --destination artifacts/browser/design-models
```

Upload the **contents** of `artifacts/browser/models/` to the chosen MinIO
bucket/prefix, preserving paths:

```text
manifest.json
v1/
  typescript/
    <weight-sha256>.onnx
    <metadata-sha256>.json
  css/
    <weight-sha256>.onnx
    <metadata-sha256>.json
  ...
```

The exporter checks both files and preserves existing revisions. Uploading only
the ONNX files is insufficient: metadata contains matching labels, decoder and
window policy. `manifest.json` is a deployment inventory; the client uses its
package-pinned paths and does not discover arbitrary remote model versions.
New releases can coexist at the same base URL because paths include file hashes.
Publish the corresponding new files before deploying a new client package.

Use model IDs in `--models`. `typescript,css` covers TSX and SCSS, and `vue`
automatically includes both child models. Omitting `--models` exports the full
catalog for apps with a general-purpose language picker. If you deploy a subset,
pass a matching `languages` list to the frontend.

For a quick same-origin Vite preview, copy the export into the consumer project's
`public/models/` directory and set `modelBaseUrl: "/models/"`. Vite copies
`public/` into the production output. For a zero-ONNX app deployment, serve that
directory separately and use its URL or mount it at `/models/` on the host.

### Private objects / temporary download URLs

Provide `resolveAssetUrl` instead of a public base URL. The callback runs on the
main thread and may return a string, URL or Promise. It receives `modelId`,
`kind` (`metadata` or `model`), `path` and `sha256`:

```ts
const highlighter = createHighlighter({
  languages: ["tsx", "scss"],
  resolveAssetUrl: async ({ path }) => {
    // Application-owned signing endpoint; not supplied by this library.
    const response = await fetch(`/api/model-url?path=${encodeURIComponent(path)}`);
    if (!response.ok) throw new Error("Unable to obtain a model download URL");
    const { url } = await response.json();
    return url;
  },
});
```

The endpoint returns a URL only; the browser still downloads the metadata/model
directly from MinIO. Have the endpoint check access and match the requested path
against the deployed model inventory before signing it. Sign the exact path,
including its file hash. The same callback handles metadata and weights.
A failed model load clears the cached URL so a subsequent attempt can obtain a
fresh signature. The library does not store or require MinIO credentials.

### Troubleshoot downloads

| Symptom                | What to check                                                                                                                               |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `404`                  | The base URL includes the correct bucket/prefix and both hashed files are present under `v1/`.                                              |
| `403`                  | The object is readable or its temporary URL is still valid.                                                                                 |
| Network error          | The resource host is reachable from the browser and its CORS policy allows the app origin.                                                  |
| Integrity mismatch     | The app package and deployment assets came from the same build. Upload the exact exported bytes.                                            |
| Failed first highlight | Keep the source visible and let the user retry after the resource host recovers. See [model caching](model-cache.md#handle-loading-errors). |

In the browser Network panel, the first use of a remote language requests its
metadata and ONNX. Try a different model to verify on-demand loading. Use a
fresh browser session or turn off **Remember downloads** in the Playground to
check delivery when the library's persistent cache would otherwise serve it.

### Verify remote delivery

The [remote example](../examples/remote/main.js) builds without `@nsh/models` and
emits zero ONNX files. Pass its deployed resource root as `?models=<URL>`. The
optional `reference` query parameter is a developer-only frozen-result check.
The consumer check also builds this example; `--reference <reference.json>` copies
an existing reference file into its test output without generating a new baseline.

[Recorded remote verification](model-delivery-verification.json) includes all
three independent builds and 410/410 exact browser/native comparisons. The full
run fetched each of the 40 weight files and 40 metadata sidecars once via direct
cross-origin GET requests; no source text was sent to the model resource host.

Cross-origin HTTP verification uses a local static resource server with CORS;
it verifies browser downloads, integrity and composition without installing a
MinIO server. An actual MinIO deployment still needs its reachable object URLs,
access policy and CORS configuration.
