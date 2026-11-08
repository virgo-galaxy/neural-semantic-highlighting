# Browser runtime verification

On 2026-11-09, all **13 selected models** were exported without retraining or
quantization, then exercised in a real Chromium browser on macOS arm64. The
[verification record](browser-verification.json) lists hashes, per-pack numerical
errors, source byte lengths and individual smoke timings.

## What was checked

1. Every ONNX graph passed the ONNX checker and CPU ORT comparisons against the
   selected original PyTorch model at 1, 2, 7, 31, 64, 127, 511 and 512 bytes.
   Every head's maximum absolute logit error was below `1e-4`.
2. All 72 existing Playground source examples, plus four edge cases, produced
   **76/76 exactly equal results**: original UTF-16 offsets, semantic types and
   modifiers. This includes JS/TS/JSX/TSX, Go, CSS/SCSS/Less, HTML/Vue composition,
   Python, Shell Here Documents/functions, Perl, AWK, SQL, PowerShell, BAT and
   Assembly. Edge cases cover empty input, CRLF, non-ASCII/astral characters and
   a long source spanning multiple 512-byte windows.
3. `@nsh/core`, `@nsh/html`, `@nsh/browser` and `@nsh/highlighter` were packed into
   **local** npm tarballs. An independent React 19.3.1 / Vite 8.2.2 project outside
   the workspace installed these archives using npm and built successfully.
   Its consumer imports only the highlighter API and theme, without repository
   aliases or a Vite highlighting plugin.
4. That React **production build**, served by a static GET-only Node server,
   displayed highlighted TSX and repeated the same **76/76 exact comparisons**.
   Worker, ONNX, MJS and WASM files loaded from emitted application assets. No
   Python service, language SDK, remote inference route or CDN was used.
5. A separate explicit-TypeScript build emitted **one ONNX model**, not all 13.
   The current Vue Playground also ran browser inference and composed Vue output.
6. `make check` passed, including 129 TypeScript tests and the existing Gold,
   training-data and Python checks. Artifact integrity tests compare all original
   selected model hashes, ONNX hashes, shipped copies and descriptor metadata.
   The preserved earlier Bash artifact was also checked unchanged.

## Scope and limits

This is conversion and integration evidence, **not a new model quality score**.
Existing classification limits remain in each pack's reports. Small floating-point
differences can affect near-tied predictions outside these examples; exact parity
is not claimed for every possible input or browser.

Only Chromium on this host and Vite production bundling were exercised. Safari,
Firefox, mobile devices, other bundlers and restrictive CSP deployments have not
yet been verified. There is no WebGPU path or old-browser fallback. Consumers
must use HTTPS or localhost and support module Workers, WebAssembly SIMD and Web
Crypto. No cross-origin isolation is required by the single-thread configuration.

Current weights remain float32, about 3.7 MB per model. Shared WASM is about
14.8 MB uncompressed / 3.9 MB gzip. First-use latency includes model/engine fetch
and initialization; recorded local timings are not a network or device benchmark.
Reuse a highlighter to reuse its worker and sessions. Close it to release them.

Reproduce export and parity with [training/browser](../training/browser/README.md).
Use `pnpm pack:browser` and the [React component](../examples/react/CodeBlock.tsx)
to check a consumer against local packages. Nothing was published and repository
visibility was not changed.
