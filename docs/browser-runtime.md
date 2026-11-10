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

## PHP addition

PHP is the eighteenth model. Its [verification record](php-browser-verification.json)
retains hashes, numerical export and additive browser/package checks.

- **115/115** examples/edges across all models matched native CPU spans, offsets,
  modifiers and child document kinds exactly, including eight PHP/template sources.
- A fresh external Vite 8.2.2 project installed four private local tarballs from
  cache, built through public imports and passed **12/12** PHP checks. This covers
  tagged/tagless PHP, heredoc/nowdoc, PHP/HTML/JS/CSS composition, empty input,
  BOM, CRLF, Unicode and long source, with exact rendered original text.
- Selective PHP emitted **four ONNX assets**: PHP and the existing HTML/JS/CSS
  models. Only predicted PHP HTML regions trigger child inference. The browser
  uses no PHP/Python process, server, runtime parser or source tag scanning.
- Full `make check` passed 147 frontend tests, six PHP teacher tests, six PHP
  composition tests, theme distribution/contrast checks and existing native tests.
  All 35 prior native/browser artifacts remain byte-identical. Theme palettes gain
  `trait`/`constant` roles using existing type/enum-member colors in all six modes;
  earlier role colors and previous verification records are preserved.
- No PHP interpreter, SDK, Composer, web server or global package was installed.
  No console warnings/errors were observed in Playground, parity or the independent
  fixture. Six preset/mode combinations were observed without rerunning inference.

[PHP quality](../packs/php/model/BENCHMARKS.md) separates base PHP/region scores
from visible composed template scores. [Known limits](../packs/php/model/KNOWN_ISSUES.md)
include interpolation, heredoc and region/fragment boundaries. Browser parity does
not remove those limits. All data/experiments remain; nothing was published.

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

## Svelte addition

Svelte is the nineteenth model. Its [verification record](svelte-browser-verification.json)
records the conversion, package build, UI checks and preservation evidence.

- **123/123** examples/edges across all models matched native CPU spans, offsets,
  modifiers and child document kinds exactly, including eight Svelte components.
  All 115 previous native reference results remain unchanged.
- A separate temporary consumer installed four private tarballs using only the
  existing offline cache and public imports, then passed **12/12** Svelte cases.
  These cover scripts, control blocks, snippets, directives, CSS/SCSS/Less, empty
  input, BOM/CRLF/Unicode and long components; source text is preserved exactly.
- Selective Svelte emits **three ONNX assets**: Svelte and existing JS/TS/CSS
  models. Regions are selected by the Svelte neural model; expressions use a fixed
  TS wrapper. No runtime compiler, regex region scanner, Python/server provider or
  source execution is used. Attribute values remain opaque by contract.
- Full `make check` passed **154 frontend tests**, six Svelte teacher tests and
  all existing checks. Seven composition tests cover routing, original UTF-16,
  clipping, child errors and invalid offsets. The teacher separately passes all
  20 independent marked Golden cases.
- ONNX numerical checks pass at all eight lengths, with maximum absolute head
  error below `2.70e-5`. The selected model has **894,614 parameters** and the same
  512-byte context. No quantization or retraining occurs during conversion.
- The Playground selects/shuffles/edits Svelte through its existing workspace
  highlighter. Light/dark switching, original source, child document kinds and six
  preset/mode combinations were verified with no browser warnings/errors.
- All 37 previous native/browser/retired model artifacts have identical hashes.
  Earlier corpora, Gold snapshots, experiments and 140 original frozen source
  families remain preserved; the boundary revision extends the map to 160.
- No Svelte npm dependency, SDK, global tool or preprocessor was installed; the
  offline official compiler bundle uses existing Node and stays in ignored cache.
  Repository/packages remain private and unpublished.

[Svelte evaluation](../packs/svelte/model/BENCHMARKS.md) keeps the small natural
base holdout (**88.47%, nine files**) separate from visible composed development
examples (**97.53%, eight files**). These scopes must not be presented as one
accuracy figure. [Known issues](../packs/svelte/model/KNOWN_ISSUES.md) retain the
remaining snippet, entity, binding and mixed-region boundary limits.

## Rust addition

Rust is the twentieth model. Its [verification record](rust-browser-verification.json)
retains the update, conversion, package and Playground evidence.

- **131/131** examples/edges across all models match native CPU spans, original
  UTF-16 offsets and modifiers exactly, including eight Rust sources. All 123
  previous reference results remain unchanged.
- A fresh temporary Vite consumer installs four private local tarballs from the
  existing offline cache, builds through public imports and passes **12/12** Rust
  cases. `rust` / `rs`, empty input, BOM/CRLF/Unicode and long source preserve
  exact spans and rendered text. Six preset/mode combinations were verified.
- Selective Rust emits **one ONNX asset**. Its eight numerical length checks have
  maximum absolute head error below `2.37e-5`; conversion does not retrain or
  quantize the 894,743-parameter, 512-byte model.
- Full `make check` passes 154 frontend tests, eight Rust teacher tests and all
  existing checks. The offline teacher passes all 23 independent marked cases.
- Existing stable Rust was updated at the user's request: Rust/Cargo 1.99.1 and
  rustup 1.29.3. Six authored metadata-only compiler probes cover common
  2018/2021/2024 source, C strings and modern 2024 forms; all eight display files
  also pass Rust 2024 metadata checks. No Cargo dependency/nightly or extra SDK
  is installed; collected libraries never build/run or execute procedural macros.
- Playground selection, shuffle, edit/blur highlighting, original text, light/dark
  and the pinned monochrome Devicon's dark-mode contrast were checked. The page,
  parity harness and independent consumer have no browser warnings/errors.
- All 39 earlier native/browser/historical model artifacts have unchanged hashes.
  Every earlier corpus, Gold snapshot and experiment remains; 192 initial Rust
  source-family assignments are retained and extended to 208 before refinement.
- Browser consumers require no Rust, Cargo, Python provider, parser, source-regex
  repair or new highlighting service. Repository/packages remain private and no
  package is published.

[Rust quality](../packs/rust/model/BENCHMARKS.md) separates natural test
(**94.90%, 15 files**) from focus and visible development code. The mixed
raw/format-string probe remains weaker; [known issues](../packs/rust/model/KNOWN_ISSUES.md)
record literal boundaries, macros and local symbol-role approximations. Runtime
parity is consistency evidence, not a claim of perfect language semantics.

## Zig addition

Zig is the twenty-first model, targeting **0.17.1 only**. Its
[verification record](zig-browser-verification.json) retains the evidence:

- **139/139** examples/edges across all models match native CPU spans, original
  UTF-16 offsets and modifiers exactly, including eight current Zig examples.
  The previous 131 reference results remain unchanged.
- A fresh temporary Vite consumer installs the four private local tarballs from
  the existing offline cache and passes **12/12** Zig cases using only public
  imports. Empty input, BOM/CRLF/Unicode and long source preserve original text.
  All six preset/mode combinations render; selective Zig emits **one ONNX asset**.
- Eight numerical export lengths pass with maximum head error below `1e-4`,
  without quantization or training. Existing native/browser model files are
  unchanged; 41 previous artifact hashes are checked.
- Full `make check` passes 154 frontend tests, nine Zig teacher tests, all 23
  independent marked Golden cases and existing data/runtime checks. The neural
  model itself is exact in 10/23 Golden cases; teacher tests are separate evidence.
  A missing generic declaration in the contextual-call fixture was corrected
  after first test without changing training data or frozen model weights.
- The user-authorized host upgrade changed Zig 0.14.1 to 0.17.1. Homebrew 7.0.13,
  required LLVM/LLD 22.1.8 and associated dependencies are recorded; LLVM
  postinstall completes and the old Zig keg remains. An upgrade probe, 42 task
  family representatives and all eight displayed sources pass the current SDK.
  Collected projects never compile or run during supervision.
- Offline labels use this exact official SDK's AST/tokenizer/primitive metadata
  and source-only `zig ast-check`. No historical release or master source is
  mixed in. All 77 original source-family assignments and both Gold/prepared
  revisions remain preserved.
- Playground selection, shuffle, editing and light/dark rendering are verified
  with original source preserved and no console warnings/errors. Browser
  inference requires no Zig SDK, compiler, Python provider or language parser.

[Zig quality](../packs/zig/model/BENCHMARKS.md) separates natural test
(92.51%, 21 files), focus tasks and visible development examples (97.26% aggregate).
[Known issues](../packs/zig/model/KNOWN_ISSUES.md) retain quoted-identifier,
literal-boundary, inferred/local-role and 512-byte-context limits. This single
release's source is bounded evidence, not universal application compatibility.
All packages and the repository remain private; nothing is published or pushed.
