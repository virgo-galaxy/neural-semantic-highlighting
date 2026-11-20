# Playground model loading

Run the existing workspace Playground at `http://127.0.0.1:3000/`. It uses the
public highlighter package in both modes and never starts a Python inference
provider. Expand **Model loading** above the code block:

- **Website assets** uses the optional local model package, fetched on demand.
- **Remote host** uses `modelBaseUrl`. Enter the resource directory URL, including
  the MinIO bucket/prefix if applicable. Absolute HTTP(S) and relative URLs work;
  query/fragment URLs are not directory roots. Private signing callbacks remain
  an integration option in the library, rather than executable UI input.
- **Remember downloads** controls the library's persistent model cache. Shared
  browser HTTP caching is separate. Click **Apply** to change loading settings.
- **Clear model cache** closes the current runtime, clears only the library's
  persistent resources and highlights again. It preserves the selected language
  and edited source. This is not a delete action on training data or source files.

Applying a source change preserves code and language selection, cancels the old
runtime and rejects stale initialization/results. A failed load leaves escaped
plain source visible with an error and **Retry highlighting**. Retrying does not
change the host: fix a deployment problem or apply a corrected URL first.

The local mode remains the default on reload; resource URLs and credentials are
not saved in browser settings. The demo supports both modes, so its production
build includes the local models needed for Website assets. A remote-only consumer
does not include those ONNX files; the independent remote example verifies that
separate deployment shape.

Theme presets and light/dark controls keep the same behavior. All model downloads
and inference happen in the browser. Cross-origin resources need their normal
CORS/access configuration; no backend model proxy or source-upload route is used.

After adding package exports or workspace packages, restart an already-running
Vite development server so it rereads package resolution metadata. For a fresh
session, `pnpm dev` builds the workspace packages before starting the Playground.

[Verification](playground-model-loading-verification.json) records local/remote
loading, failure/retry, cache clearing, keyboard controls and the 390-pixel frame
viewport check. It is not a physical mobile-device performance benchmark.
