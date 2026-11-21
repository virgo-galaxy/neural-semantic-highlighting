# Playground build and model loading

Use `pnpm dev` for local development at `http://127.0.0.1:3000/`. React renders
the Playground using the published Virgo Design components and theme. The model
runtime runs in a browser Worker.

The first TypeScript example has a precomputed preview from the verified model
reference. Changing languages or examples starts inference for that content.
After an edit, inference starts automatically when typing pauses for 350 ms.
Press Control/Command + Enter to update the preview immediately. The browser
downloads the needed ONNX files and shared WASM from the deployment's static
assets. Previously used models can be served from the browser cache.

Use a production build to verify the static output:

```bash
pnpm install --frozen-lockfile
pnpm build
```

On Vercel, import the repository with its root directory selected and enable
`ENABLE_EXPERIMENTAL_COREPACK=1` to use the pinned pnpm version. The root
`vercel.json` selects `apps/playground/dist` as the static output. That directory
contains the app and all 40 ONNX models as separately requested files.

To test a separate resource host and signed URLs in a consuming app, see
[model delivery](model-delivery.md). The
[historical verification](playground-model-loading-verification.json) records
tests of the previous Playground's model-source controls.
