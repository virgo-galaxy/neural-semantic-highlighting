# Browser runtime verification

The original rollout on 2026-11-09 exported **13 selected models** without retraining or
quantization, then exercised in a real Chromium browser on macOS arm64. The
[verification record](browser-verification.json) lists hashes, per-pack numerical
errors, source byte lengths and individual smoke timings.

## Original rollout checks

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

## Java addition

Java is the fourteenth selected model. Its own
[verification record](java-browser-verification.json) preserves the native/ONNX
hashes and additive checks; the original record above remains unchanged.

- The float32 Java export passed ONNX checking and eight CPU PyTorch/ORT head
  comparisons, with maximum absolute error `3.0517578125e-5`.
- A real Chromium browser produced **83/83 exact span/role/modifier matches**
  against native CPU references: all prior cases plus seven Java examples.
- A fresh external vanilla-JS project installed four local private tarballs from
  the npm cache, imported only public package paths, and built with Vite 8.2.2.
  Its emitted static build passed **11/11 Java comparisons**, including empty
  input, CRLF, Unicode/astral characters and source beyond the 512-byte window.
  Rendered text matched the original input exactly. A renderer regression fix
  preserves carriage returns through HTML parsing, with highlighted/gap tests.
- The Java-only consumer emitted **one ONNX model** and exercised all three
  theme presets in light/dark mode. No Python process or JDK participates in
  browser inference. No additional highlighting server or port was introduced.
- Final `make check` passed **141 TypeScript/JavaScript tests**, all existing
  native Gold/data checks, six Java teacher tests and 17 independent Java Golden
  cases. All 27 prior native/browser model artifacts remain byte-identical.

This adds runtime/packaging evidence, not another model-accuracy evaluation.
Java quality and remaining source-display errors are in its
[model reports](../packs/java/model/BENCHMARKS.md) and
[known limits](../packs/java/model/KNOWN_ISSUES.md). Packages and repository remain
private; no npm publication took place.

## C# addition

C# is the fifteenth model. Its [verification record](csharp-browser-verification.json)
keeps the export hashes, numerical comparisons and additive browser checks.

- All **91/91** existing/example/edge cases, including eight C# examples, matched
  native CPU semantic spans, offsets and modifiers exactly in Chromium.
- A fresh external Vite 8.2.2 project installed the four private local tarballs
  from cache, built, and passed **12/12** C# checks through public package paths.
  This covers `csharp`/`cs`/`c#`, BOM, CRLF, Unicode, empty input and long source.
  Original rendered text was preserved; six theme/mode combinations were observed.
- The selective C# build emitted **one ONNX model**. No .NET SDK, Mono, Python
  process or offline grammar is used by browser inference. The Mac environment
  received no .NET/Mono or global parser package installation.
- Final `make check` passed 141 frontend tests, the seven C# teacher tests and
  existing native Gold/data checks. All 29 earlier native/browser models remain
  byte-identical. The 22 marked Golden cases validate the teacher, not a claim of
  perfect neural output; measured model limits remain explicit.

Model quality is separate in the [C# report](../packs/csharp/model/BENCHMARKS.md)
and [known issues](../packs/csharp/model/KNOWN_ISSUES.md). Original verification
records, datasets and runs remain preserved. No package was published.

## C addition

C is the sixteenth model. Its [verification record](c-browser-verification.json)
retains export hashes, numerical comparisons and additive end-to-end checks.

- **99/99** example/edge cases across all models matched native CPU spans,
  offsets and modifiers exactly in Chromium, including eight new C/C-header probes.
- A fresh external Vite 8.2.2 project installed four private local tarballs from
  cache, built through public package imports and passed **12/12** C cases.
  Empty input, BOM, CRLF, Unicode and long source retained exact rendered text.
  All six theme/mode combinations were observed; selective C emitted one ONNX.
- Full `make check` passed 141 frontend tests, six C teacher tests and all existing
  Gold/data/runtime checks. All 31 prior native/browser artifacts remain
  byte-identical, including the historical Bash model.
- The existing Apple Clang/SDK compiled authored C11/C17/C23 probes and built the
  offline grammar. No compiler, SDK or global package was installed. The frontend
  uses no compiler, SDK, parser, preprocessor or Python provider. No console
  warnings/errors were observed in the Playground, parity or independent fixture.

[Model quality](../packs/c/model/BENCHMARKS.md) and
[known limits](../packs/c/model/KNOWN_ISSUES.md) are separate from runtime parity.
Original records, datasets and experiments remain preserved. No package was
published and repository visibility was not changed.

## C++ addition

C++ is the seventeenth model. Its [verification record](cpp-browser-verification.json)
retains export hashes, numerical checks and additive end-to-end results.

- **107/107** example/edge cases across all models matched native CPU semantic
  spans, offsets and modifiers exactly, including eight C++ display sources.
- A fresh external Vite 8.2.2 project installed four private local tarballs from
  cache, built through public package paths and passed **13/13** C++ cases.
  `cpp`/`c++`/`cxx`, explicit C++ `.h`, empty input, BOM, CRLF, Unicode and long
  source retained exact rendered text. Six theme/mode combinations were observed.
- The selective C++ build emitted **one ONNX model**. Full `make check` passed
  141 frontend tests, eight C++ teacher tests and all existing Gold/data checks.
  All 33 prior native/browser artifacts remain byte-identical, including C/C#
  and the historical Bash model. Earlier verification records remain unchanged.
- Existing Apple Clang/SDK probes compiled and ran; no compiler, SDK or global
  package was installed. Browser inference uses no compiler, parser, SDK,
  preprocessor or Python provider. No console warnings/errors were observed in
  the Playground, parity harness or independent production fixture.

Language quality is separate in [the C++ report](../packs/cpp/model/BENCHMARKS.md)
and [known limits](../packs/cpp/model/KNOWN_ISSUES.md), including raw strings and
local/template roles. Original data and every experiment remain preserved.
No package was published and repository visibility did not change.

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
