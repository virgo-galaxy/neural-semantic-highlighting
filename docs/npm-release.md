# npm release preparation

The first release candidate is a single unscoped package,
`neural-semantic-highlighting`. Its archive includes the frontend API, Core,
HTML renderer, browser Worker/WASM and generated themes. ONNX Runtime Web is a
normal npm dependency. The archive contains zero model weights. The app can
serve selected models alongside its own assets or load them from a separate
host. [Model delivery](model-delivery.md) covers both deployments.

The workspace retains its `@nsh/*` modules and the Playground uses them directly.
The packer combines their compiled files in a staging directory and resolves
internal JavaScript imports and TypeScript declarations within the archive.
Candidate manifests retain `private: true`.

## Build and verify a candidate

Use a fresh checkout with Node.js 24 and the pnpm version recorded in the
lockfile:

```bash
pnpm install --frozen-lockfile
pnpm all
pnpm pack:browser
node scripts/check-model-delivery.mjs
```

`pnpm all` runs builds, type checking, lint, formatting, tests and the
portable-path check. `pnpm pack:browser` writes the single local archive
and its file inventory to `artifacts/browser/npm-release/`.

Review `artifacts/browser/npm-release/archives.json` and
`artifacts/browser/npm-release-check/verification.json`. The check installs
the archive in independent projects, type-checks the public API and builds
Vite examples. Each build emits zero ONNX files and one shared WASM.
Review the file list for built runtime assets, license notices and accidental
training files, credentials or machine-specific paths.

Export models from the same revision:

```bash
node scripts/export-model-assets.mjs
```

Serve `artifacts/browser/npm-release-check/remote/` as the app root and
point `?models=<URL>` at the exported model directory. The default model URL is
`/models/`. Check highlighting in the browser. For a separate origin, verify
CORS on both the JSON metadata and the ONNX files. Keep their paths together.

To compare browser output with a recorded reference, pass `--reference <path>`
to the consumer check and open the remote example with
`&reference=reference.json` (or `?reference=reference.json` without other
parameters).

## Before publishing

Confirm the publishing account can claim the unscoped name and complete npm
authentication. Confirm the archive contains the MIT `LICENSE`, the
`"license": "MIT"` manifest field and the ONNX Runtime license notice.
Document how users can obtain and serve matching models. Review model
redistribution terms independently of the engine license.

Once approved, update the candidate's version, installation command
and resource links. Review the exact archive again. After release, test a
registry install in a fresh frontend app.
