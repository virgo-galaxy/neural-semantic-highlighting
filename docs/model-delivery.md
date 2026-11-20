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
allow the application origin. HTTP compression is optional. Shared WASM still
ships with `@nsh/browser` as an application asset.

### Export the deployable directory

After building workspace packages:

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
directly from MinIO. Sign the requested path exactly, including its file hash.
A failed model load clears the cached URL so a subsequent attempt can obtain a
fresh signature. The library does not store or require MinIO credentials.

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
