# Browser runtime verification

## Current verified state

The latest [Makefile record](makefile-browser-verification.json), dated
2026-11-18, covers **37 selected model packs** and **361/361** exact
Chromium/native span/role/modifier comparisons, with **177** passing frontend
tests. The independent Makefile-only consumer passes **12/12** comparisons,
element/tokens APIs, six preset/mode combinations and custom CSS, emitting one
model asset. All 348 previous reference cases remain unchanged. Earlier
language-specific records remain below; XML/SVG and JSON/JSONC each share one
model, and Flutter uses Dart.

The Playground and frontend package run the selected ONNX models in a browser
Worker, without a Python provider or language SDK. Packages remain private and
unpublished; local tarballs are the supported installation route before release.
See the [consumer README](../README.md) for current usage and the
[scope and limits](#scope-and-limits) for unverified browsers/deployments.

The sections below are historical rollout records. Counts, artifact hashes,
checks and statements about publication or pushing describe each addition at the
time it was verified, rather than the current repository totals or Git status.

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

## Dart addition

Dart is the twenty-second model. Its [verification record](dart-browser-verification.json)
retains browser, private-package and Playground evidence without an installed
Dart/Flutter SDK:

- **147/147** examples/edges across all models match native CPU spans, original
  UTF-16 offsets and modifiers, including eight Dart examples. The previous 139
  reference results remain unchanged.
- A fresh temporary Vite consumer installs the four private local tarballs from
  the existing offline cache and passes **12/12** Dart cases using public imports.
  Empty input, BOM/CRLF/Unicode and long source preserve original text. All six
  palette/mode combinations render; selective Dart emits **one ONNX asset**.
- Eight numerical export lengths pass with maximum head error below `1e-4`,
  without retraining or quantization. All 43 previous native/browser/historical
  artifact hashes remain unchanged.
- Full `make check` passes 154 frontend tests, eleven Dart teacher tests, all 35
  independently marked Golden cases and the existing data/runtime checks. The
  neural model itself is exact in 6/35 visible Golden cases; teacher exactness is
  separate from neural quality and includes declaration modifiers.
- No Dart/Flutter SDK, analyzer, pub environment or global dependency is installed.
  Existing Apple Clang builds the pinned independent Tree-sitter grammar in
  ignored project cache. Generated C source, licenses, Git blobs, compiler and
  library hashes are retained. No source project, import, generator or annotation
  is executed; displayed source has parse/coverage evidence only, not SDK checks.
- The capture pins 212 Dart-package/Flutter-stable source files. Initial 94 family
  assignments remain intact; eight bounded literal/context families extend the
  frozen map to 102. All original source/Gold/prepared revisions and training
  runs remain preserved. No training follows the frozen candidate's first test.
- Playground selection, shuffle, edit/blur and light/dark themes preserve original
  source without console warnings/errors. Common Flutter code uses the same Dart
  entry. Frontend inference needs no SDK, Python provider or language parser.

[Dart evaluation](../packs/dart/model/BENCHMARKS.md) separates natural test
(94.22%, 20 files), focus and visible development examples (89.36% aggregate;
Flutter widget 96.85%, mixed strings 85.34%). [Known issues](../packs/dart/model/KNOWN_ISSUES.md)
retain raw/triple/interpolated literal boundaries, inferred/local/constructor
roles, complex patterns and context limits. Independent grammar acceptance does
not certify complete SDK-version compatibility or resolve imported widgets.
All packages and the repository remain private; nothing is published or pushed.

## Flutter entry using Dart

Flutter adds a dedicated UI/public entry and eight examples while retaining the
22 existing models. Its [verification record](flutter-browser-verification.json)
records the shared-model behavior:

- **155/155** browser cases match native CPU spans, original UTF-16 offsets and
  modifiers, including eight new Flutter examples; all prior 147 results remain
  unchanged. All 45 previous model artifact hashes remain identical.
- A fresh offline consumer builds the four private local tarballs with public
  imports and passes **12/12** cases across `flutter`, `dart` and `Flutter` names.
  `highlightTokens` and `highlightElement` on `language-flutter` also match native
  results. Text, BOM/CRLF/Unicode and long input are preserved.
- Selective `@nsh/highlighter/languages/flutter` re-exports Dart and emits **one
  Dart ONNX asset**. Importing Dart and Flutter together deduplicates that model.
  Results/HTML use canonical `dart`; six light/dark palette combinations work.
- Full `make check` passes 155 frontend tests and twelve Dart/Flutter teacher
  tests, including 35 unchanged Dart marked cases and eight new Flutter probes.
  Strict neural exactness is 0/8 new probes, recorded separately from span F1.
- New application review covers 48 pinned official Flutter sample files from
  twelve projects, with 93.95% exact-span F1 and no exact/lexical/shape matches in
  prior Gold. Eight independent display examples aggregate 95.73%. This additional
  review does not replace the historical Dart held-out test.
- These measurements support reusing the frozen Dart weights. No training,
  new model export, SDK, pub environment, analyzer, source project execution or
  parser dependency is added to inference. Review sources remain outside training
  under the existing external Dart dataset root, with licenses and source locks.
- Playground selection, shuffle, editing/blur and light/dark themes preserve
  source and canonical Dart routing without console warnings/errors.

[Flutter usage/evaluation](../packs/dart/model/FLUTTER.md) explains shared CSS,
source-local roles, strict Golden diagnostics and existing model limits. Imported
widget types, versions and generated code are not resolved. Existing data,
checkpoints, models and reports remain preserved. Packages/repository stay private;
nothing is published or pushed as part of this addition.

## Swift addition

Swift is the twenty-third selected model. Its [verification record](swift-browser-verification.json)
preserves the selected native/browser hashes and additive checks.

- The float32 export passes ONNX checking and all eight CPU PyTorch/ORT head
  comparisons, from 1 through 512 bytes, within the existing `1e-4` tolerance.
- Real Chromium browser inference matches **167/167** original UTF-16 span, role
  and modifier references: every prior case, eight new Swift/SwiftUI displays and
  four Swift empty/CRLF/Unicode/long multi-window probes.
- An independent temporary frontend installs four local npm archives and cached
  Vite completely offline. Its production build uses public imports and **one
  Swift ONNX asset**, without repository aliases. The prebuilt static output is
  accessed through the existing local Playground server; no new service or port
  is introduced. It passes **12/12** Swift comparisons and original-text checks.
- Case-normalized Swift IDs, `highlightElement`, `highlightTokens`, six theme/mode
  combinations and a public custom CSS color override are verified. The Playground
  exposes Swift with the pinned Devicon icon, eight examples, shuffle and light/dark
  controls. No browser console errors were observed.
- `make check` passes all **155** TypeScript/JavaScript tests and existing native
  checks, including **12** Swift teacher tests and **28** independent Golden cases.
  All **44** earlier native/ONNX weight files remain byte-identical.

The selected model's natural test F1 is **93.65%** across 22 files; displayed
examples aggregate **92.16%** and the two common SwiftUI examples score about
97.7%. [Quality and known limits](../packs/swift/model/BENCHMARKS.md) distinguish
these from parity: mixed literal boundaries, dollar names and local semantic roles
remain approximate. Browser consumers require no Swift SDK, Xcode, parser or
Python process. The repository and packages remain private and unpublished.

## Kotlin addition

Kotlin is the twenty-fourth selected model. Its [verification record](kotlin-browser-verification.json)
retains conversion, browser parity, independent package and preservation evidence.

- Real Chromium browser inference matches **179/179** original UTF-16 spans, roles
  and modifiers, including all earlier cases, eight Kotlin/code-script displays
  and four empty/CRLF/Unicode/long multi-window Kotlin probes.
- An independent temporary Vite application installs four local package archives
  offline and imports public core + Kotlin + themes exports. Its static build
  emits **one Kotlin ONNX asset**, without repository aliases, and passes **12/12**
  span and original-text checks. It is served through the existing Playground
  filesystem route, with no new server or port.
- `kotlin`, `Kotlin`, `kt`, `kts`, `kotlin-script`, `highlightElement` on a
  `language-kts` element, `highlightTokens`, six preset/mode combinations and a
  custom CSS override all pass. Playground adds the pinned Devicon icon, eight
  examples, shuffle and light/dark switching through the existing browser worker.
- Full `make check` passes **156** frontend tests and all previous language checks,
  including **13** Kotlin teacher tests and **32** independent marked Golden cases.
  All 46 earlier native/ONNX files remain byte-identical.

The first code/script natural test is **94.57%**
across 31 files; visible examples aggregate
**92.74%**. The neural model is entirely
exact in 16/32 Golden cases. [Evaluation and limits](../packs/kotlin/model/BENCHMARKS.md)
keep these evidence sets separate. Raw/multi-dollar template boundaries, imported
calls, implicit receivers and local roles remain approximate. Offline Gold reuses
the existing JDK with official Kotlin 2.4.21 Maven components in project cache;
no Kotlin SDK, Gradle, Android SDK or global dependency is installed. Browser
consumers require none of these tools or a Python process.

## R addition

R is selected model 25. The [verification record](r-browser-verification.json)
retains ONNX conversion, browser/native parity and independent public-package evidence.

- Chromium matches **191/191** original UTF-16 span/role/modifier references,
  including all earlier cases, eight new displays and four empty/CRLF/Unicode/long
  multi-window probes. These are consistency checks, not additional accuracy tests.
- An independent temporary Vite app installs four local package archives offline,
  imports public core + r + theme exports, and emits **one model asset** without
  repository aliases. It passes **12/12** spans/original-text comparisons,
  `highlightElement`, `highlightTokens`, case-normalized IDs, six preset/mode
  combinations and custom CSS. Static output uses the existing Playground
  filesystem route; no new server/port is introduced.
- Playground adds the pinned Devicon icon, eight examples, shuffle and light/dark
  switching through the existing browser worker, without Python. Full `make check`
  passes **156** frontend tests and every prior language check,
  including **10** new teacher tests and **32** marked Golden cases.
  All 48 earlier native/ONNX weight files remain byte-identical.

Natural held-out F1 is **96.04%** on
15 real files. Visible displays aggregate
**92.52%**; strict neural Golden agreement is
13/32. [Quality and limits](../packs/r/model/BENCHMARKS.md)
keep these evidence sets distinct. Long raw/delimited strings, backtick names, comments, closure and dynamic-call roles remain approximate. Formula names, tidy evaluation/NSE, environments/promises and S3/S4 dispatch are source-local approximations, without R package/type resolution. Offline tools are
r-lib tree-sitter-r 1.3.0 and Tree-sitter 0.25.10, compiled with existing Clang only in project cache; no language SDK/global package is installed and collected projects
never execute. Frontend consumers require no language toolchain or Python process.

## Scala addition

Scala is selected model 26. The [verification record](scala-browser-verification.json)
retains ONNX conversion, browser/native parity and independent public-package evidence.

- Chromium matches **203/203** original UTF-16 span/role/modifier references,
  including all earlier cases, eight new displays and four empty/CRLF/Unicode/long
  multi-window probes. These are consistency checks, not additional accuracy tests.
- An independent temporary Vite app installs four local package archives offline,
  imports public core + scala + theme exports, and emits **one model asset** without
  repository aliases. It passes **12/12** spans/original-text comparisons,
  `highlightElement`, `highlightTokens`, case-normalized IDs, six preset/mode
  combinations and custom CSS. Static output uses the existing Playground
  filesystem route; no new server/port is introduced.
- Playground adds the pinned Devicon icon, eight examples, shuffle and light/dark
  switching through the existing browser worker, without Python. Full `make check`
  passes **156** frontend tests and every prior language check,
  including **13** new teacher tests and **33** marked Golden cases.
  All 50 earlier native/ONNX weight files remain byte-identical.

Natural held-out F1 is **89.00%** on
30 real files. Visible displays aggregate
**90.13%**; strict neural Golden agreement is
17/33. [Quality and limits](../packs/scala/model/BENCHMARKS.md)
keep these evidence sets distinct. Long plain/raw/interpolated strings, generic/type and enum/constructor roles, implicit receivers and distant symbols remain approximate. Given/using and extension syntax is source-local, without implicit search, overload resolution, macro/plugin execution, framework APIs or experimental type-system certification. Offline tools are
Tree-sitter Scala 0.26.12 with runtime 0.25.10, compiled with existing Clang only in project cache; no language SDK/global package is installed and collected projects
never execute. Frontend consumers require no language toolchain or Python process.

## Ruby addition

Ruby is selected model 27. The [verification record](ruby-browser-verification.json)
retains ONNX conversion, browser/native parity and independent public-package evidence.

- Chromium matches **215/215** original UTF-16 span/role/modifier references,
  including all earlier cases, eight new displays and four empty/CRLF/Unicode/long
  multi-window probes. These are consistency checks, not additional accuracy tests.
- An independent temporary Vite app installs four local package archives offline,
  imports public core + ruby + theme exports, and emits **one model asset** without
  repository aliases. It passes **12/12** spans/original-text comparisons,
  `highlightElement`, `highlightTokens`, case-normalized IDs, six preset/mode
  combinations and custom CSS. Static output uses the existing Playground
  filesystem route; no new server/port is introduced.
- Playground adds the pinned Devicon icon, eight examples, shuffle and light/dark
  switching through the existing browser worker, without Python. Full `make check`
  passes **157** frontend tests and every prior language check,
  including **13** new teacher tests and **33** marked Golden cases.
  All 52 earlier native/ONNX weight files remain byte-identical.

Natural held-out F1 is **86.96%** on
15 real files. Visible displays aggregate
**90.62%**; strict neural Golden agreement is
10/33. [Quality and limits](../packs/ruby/model/BENCHMARKS.md)
keep these evidence sets distinct. Heredoc/percent/regex/interpolated string boundaries, destructuring/pattern bindings, constant/type and top-level/member call roles remain approximate. Dynamic dispatch, metaprogramming, Rails/Rake DSLs, generated classes, refinements and distant scopes are source-local approximations without Ruby/gem execution or dependency resolution. Offline tools are
Tree-sitter Ruby 0.23.1 at ad907a69 with runtime 0.25.10, compiled with existing Clang only in project cache; no language SDK/global package is installed and collected projects
never execute. Frontend consumers require no language toolchain or Python process.

## Lua addition

Lua is selected model 28. The [verification record](lua-browser-verification.json)
retains ONNX conversion, browser/native parity and independent public-package evidence.

- Chromium matches **227/227** original UTF-16 span/role/modifier references,
  including all earlier cases, eight new displays and four empty/CRLF/Unicode/long
  multi-window probes. These are consistency checks, not additional accuracy tests.
- An independent temporary Vite app installs four local package archives offline,
  imports public core + lua + theme exports, and emits **one model asset** without
  repository aliases. It passes **12/12** spans/original-text comparisons,
  `highlightElement`, `highlightTokens`, case-normalized IDs, six preset/mode
  combinations and custom CSS. Static output uses the existing Playground
  filesystem route; no new server/port is introduced.
- Playground adds the pinned Devicon icon, eight examples, shuffle and light/dark
  switching through the existing browser worker, without Python. Full `make check`
  passes **157** frontend tests and every prior language check,
  including **13** new teacher tests and **32** marked Golden cases.
  All 54 earlier native/ONNX weight files remain byte-identical.

Natural held-out F1 is **91.78%** on
15 real files. Visible displays aggregate
**92.28%**; strict neural Golden agreement is
10/32. [Quality and limits](../packs/lua/model/BENCHMARKS.md)
keep these evidence sets distinct. Long/delimited string and comment boundaries, table/method roles, closure captures, dynamic metatables and distant lexical bindings remain approximate. No Lua/Neovim/LuaRocks execution, dependency resolution or full LuaJIT/Luau dialect compatibility is claimed. Offline tools are
Tree-sitter Lua 0.5.0 at 10fe0054 with runtime 0.25.10, compiled with existing Clang only in project cache; no language SDK/global package is installed and collected projects
never execute. Frontend consumers require no language toolchain or Python process.

## JSON / JSONC addition

JSON / JSONC is selected model 29. The [verification record](json-browser-verification.json)
retains ONNX conversion, browser/native parity and independent public-package evidence.

- Chromium matches **251/251** original UTF-16 span/role/modifier references,
  including all earlier cases, sixteen new displays and eight empty/CRLF/Unicode/long
  multi-window probes. These are consistency checks, not additional accuracy tests.
- An independent temporary Vite app installs four local package archives offline,
  imports public core + json + theme exports, and emits **one model asset** without
  repository aliases. It passes **24/24** spans/original-text comparisons,
  `highlightElement`, `highlightTokens`, case-normalized JSON/JSONC kinds, six preset/mode
  combinations and custom CSS. Static output uses the existing Playground
  filesystem route; no new server/port is introduced.
- Playground adds the pinned Devicon icon, sixteen examples, shuffle and light/dark
  switching through the existing browser worker, without Python. Full `make check`
  passes **158** frontend tests and every prior language check,
  including **13** new teacher tests and **48** marked Golden cases.
  All 56 earlier native/ONNX weight files remain byte-identical.

Combined natural held-out F1 is **99.78%** on
15 real files. Separately, JSON scores
**99.71%** on
9 files, and JSONC scores
**99.84%** on
6 files. Visible displays aggregate
**98.84%**; strict neural Golden agreement is
35/48. [Quality and limits](../packs/json/model/BENCHMARKS.md)
keep these evidence sets distinct. Very short empty-container/primitive and comment-plus-container snippets can merge spans or misclassify keywords. Quoted-key/value roles, escapes and long string/comment boundaries across the 512-byte context remain approximate. No schema/type validation, JSON5 syntax, embedded-string parsing, automatic format detection or runtime parser/spelling repair is provided. JSONC explicitly accepts trailing commas; strict JSON supervision rejects them and comments, while runtime highlighting itself is not a syntax validator. Offline tools are
Pinned Microsoft jsonc-parser 3.3.1 official npm assets with SHA-512/archive/per-file hashes, using existing Node only in project cache; no language SDK/global package is installed and collected projects
never execute. Frontend consumers require no language toolchain or Python process.

## YAML addition

YAML is selected model 30. The [verification record](yaml-browser-verification.json)
retains ONNX conversion, browser/native parity and independent public-package evidence.

- Chromium matches **263/263** original UTF-16 span/role/modifier references,
  including all earlier cases, eight new displays and four empty/CRLF/Unicode/long
  multi-window probes. These are consistency checks, not additional accuracy tests.
- An independent temporary Vite app installs four local package archives offline,
  imports public core + yaml + theme exports, and emits **one model asset** without
  repository aliases. It passes **12/12** spans/original-text comparisons,
  `highlightElement`, `highlightTokens`, case-normalized IDs, six preset/mode
  combinations and custom CSS. Static output uses the existing Playground
  filesystem route; no new server/port is introduced.
- Playground adds the pinned Devicon icon, eight examples, shuffle and light/dark
  switching through the existing browser worker, without Python. Full `make check`
  passes **159** frontend tests and every prior language check,
  including **14** new teacher tests and **40** marked Golden cases.
  All 58 earlier native/ONNX weight files remain byte-identical.

Natural held-out F1 is **95.34%** on
12 real files. Visible displays aggregate
**94.44%**; strict neural Golden agreement is
15/40. [Quality and limits](../packs/yaml/model/BENCHMARKS.md)
keep these evidence sets distinct. Block scalars remain a material weakness: header comments can merge into bodies, indented # lines can receive comment roles, folded bodies can fragment, and JSON-looking literal content can acquire nested property/keyword roles even within the context. Plain/quoted/block scalar and header boundaries, indentation-sensitive key/value roles, anchors/aliases/tags and multi-document context remain approximate. No alias expansion, schema/application validation, legacy YAML 1.1 type guarantee, template execution, embedded-language parsing or runtime parser/spelling repair is provided. Offline tools are
Pinned yaml 2.9.1 official npm Document/CST assets with archive/per-file hashes and retained ISC license, using existing Node only in project cache; no language SDK/global package is installed and collected projects
never execute. Frontend consumers require no language toolchain or Python process.

## TOML addition

TOML is selected model 31. The [verification record](toml-browser-verification.json)
retains ONNX conversion, browser/native parity and independent public-package evidence.

- Chromium matches **275/275** original UTF-16 span/role/modifier references,
  including all earlier cases, eight new displays and four empty/CRLF/Unicode/long
  multi-window probes. These are consistency checks, not additional accuracy tests.
- An independent temporary Vite app installs four local package archives offline,
  imports public core + toml + theme exports, and emits **one model asset** without
  repository aliases. It passes **12/12** spans/original-text comparisons,
  `highlightElement`, `highlightTokens`, case-normalized IDs, six preset/mode
  combinations and custom CSS. Static output uses the existing Playground
  filesystem route; no new server/port is introduced.
- Playground adds the pinned Devicon icon, eight examples, shuffle and light/dark
  switching through the existing browser worker, without Python. Full `make check`
  passes **160** frontend tests and every prior language check,
  including **12** new teacher tests and **40** marked Golden cases.
  All 61 earlier native/ONNX weight files remain byte-identical.

Natural held-out F1 is **99.10%** on
9 real files. Visible displays aggregate
**97.73%**; strict neural Golden agreement is
27/40. [Quality and limits](../packs/toml/model/BENCHMARKS.md)
keep these evidence sets distinct. Multiline string bodies remain a material weakness: original quoted/hash/shell-looking content can fragment or receive comment/property roles even inside the 512-byte context (strings.toml display 68.42% F1). Quoted keys containing dots can split or acquire the header role (keys.toml 91.89%). Header/assignment roles, dates and long bodies remain approximate. Common 1.0 and tested 1.1 forms do not certify every TOML edge case; the pinned parser labels 1.1 support experimental. No project validation, configuration execution, interpolation or runtime parser/spelling repair is provided. Offline tools are
Pinned toml-eslint-parser 1.0.3 and eslint-visitor-keys 5.0.1 official npm assets, with original licenses and archive/per-file hashes, using existing Node only; no language SDK/global package is installed and collected projects
never execute. Frontend consumers require no language toolchain or Python process.

## INI addition

INI is selected model 32. The [verification record](ini-browser-verification.json)
retains ONNX conversion, browser/native parity and independent public-package evidence.

- Chromium matches **287/287** original UTF-16 span/role/modifier references,
  including all earlier cases, eight new displays and four empty/CRLF/Unicode/long
  multi-window probes. These are consistency checks, not additional accuracy tests.
- An independent temporary Vite app installs four local package archives offline,
  imports public core + ini + theme exports, and emits **one model asset** without
  repository aliases. It passes **12/12** spans/original-text comparisons,
  `highlightElement`, `highlightTokens`, case-normalized IDs, six preset/mode
  combinations and custom CSS. Static output uses the existing Playground
  filesystem route; no new server/port is introduced.
- Playground adds the original INI configuration icon, eight examples, shuffle and light/dark
  switching through the existing browser worker, without Python. Full `make check`
  passes **161** frontend tests and every prior language check,
  including **12** new teacher tests and **40** marked Golden cases.
  All 63 earlier native/ONNX weight files remain byte-identical.

Natural held-out F1 is **89.70%** on
8 real files. Visible displays aggregate
**95.17%**; strict neural Golden agreement is
17/40. [Quality and limits](../packs/ini/model/BENCHMARKS.md)
keep these evidence sets distinct. Indented continuation lines resembling assignments or headers can split or gain property/punctuation roles (continuations.ini display 82.76% F1). Packaging constraints/version strings and empty-value continuations remain weaker (setup.cfg 89.47%); quoted/path values and section/glob boundaries can also fragment. Common INI/EditorConfig source uses one explicit dialect: #/; full-line comments, with inline value markers kept literal. Application-specific inline comments/escape rules and general .conf/.env syntax are outside scope. No interpolation, configuration execution, project validation or runtime parser/spelling repair is provided. Offline tools are
Existing CPython 3.12 ConfigParser with interpolation disabled, independent section/key inventory validation and Python/stdlib/teacher SHA-256 provenance; no downloaded tool or SDK; no language SDK/global package is installed and collected projects
never execute. Frontend consumers require no language toolchain or Python process.

## .env addition

.env is selected model 33. The [verification record](dotenv-browser-verification.json)
retains ONNX conversion, browser/native parity and independent public-package evidence.

- Chromium matches **299/299** original UTF-16 span/role/modifier references,
  including all earlier cases, eight new displays and four empty/CRLF/Unicode/long
  multi-window probes. These are consistency checks, not additional accuracy tests.
- An independent temporary Vite app installs four local package archives offline,
  imports public core + dotenv + theme exports, and emits **one model asset** without
  repository aliases. It passes **12/12** spans/original-text comparisons,
  `highlightElement`, `highlightTokens`, case-normalized IDs, six preset/mode
  combinations and custom CSS. Static output uses the existing Playground
  filesystem route; no new server/port is introduced.
- Playground adds the original dotenv configuration icon, eight examples, shuffle and light/dark
  switching through the existing browser worker, without Python. Full `make check`
  passes **162** frontend tests and every prior language check,
  including **12** new teacher tests and **40** marked Golden cases.
  All 65 earlier native/ONNX weight files remain byte-identical.

Natural held-out F1 is **98.25%** on
3 real files. Visible displays aggregate
**97.70%**; strict neural Golden agreement is
21/40. [Quality and limits](../packs/dotenv/model/BENCHMARKS.md)
keep these evidence sets distinct. Quoted/multiline boundaries remain a measured weakness (multiline.env display 81.82% F1), including assignment/hash-looking content within values; individual comment/value boundaries can still split (comments.env 93.33%). Declaration flags, escaped quotes and long bodies remain approximate. One common ASCII-name/equals-assignment dotenv profile is supported; loader-specific colon/dotted/dashed names are outside the teacher contract. All values remain strings. No expansion, command substitution, environment injection, decryption, application validation or runtime parser/spelling repair is provided. Offline tools are
Pinned official dotenv 18.0.10 parse-only npm assets with retained BSD-2-Clause license and archive/per-file hashes, using existing Node only; no language SDK/global package is installed and collected projects
never execute. Frontend consumers require no language toolchain or Python process.

## XML / SVG addition

XML / SVG is selected model 34. The [verification record](xml-browser-verification.json)
retains ONNX conversion, browser/native parity and independent public-package evidence.

- Chromium matches **323/323** original UTF-16 span/role/modifier references,
  including all earlier cases, sixteen new displays and eight empty/CRLF/Unicode/long
  multi-window probes. These are consistency checks, not additional accuracy tests.
- An independent temporary Vite app installs four local package archives offline,
  imports public core + xml + theme exports, and emits **one model asset** without
  repository aliases. It passes **24/24** spans/original-text comparisons,
  `highlightElement`, `highlightTokens`, case-normalized IDs, six preset/mode
  combinations and custom CSS. Static output uses the existing Playground
  filesystem route; no new server/port is introduced.
- Playground adds the Devicon XML and original SVG icons, sixteen examples and two distinct entries, shuffle and light/dark
  switching through the existing browser worker, without Python. Full `make check`
  passes **163** frontend tests and every prior language check,
  including **14** new teacher tests and **48** marked Golden cases.
  All 67 earlier native/ONNX weight files remain byte-identical.

Natural held-out F1 is **92.20%** on
13 real files. Visible displays aggregate
**98.97%**; strict neural Golden agreement is
37/48. [Quality and limits](../packs/xml/model/BENCHMARKS.md)
keep these evidence sets distinct. Natural XML test comment and string exact-span F1 are only 51.28% (15 reference comment spans) and 70.93% (69 string spans), so the aggregate must not hide difficult comment/quoted-content boundaries. The instruction-plus-nested-code CDATA display remains weak (xml/cdata.xml 78.26% exact-span F1): a processing instruction can split into keyword fragments, quoted markup inside CDATA can receive tag/text roles, and escaped closing-tag text can merge entity boundaries. Atom text/whitespace and public-doctype boundaries also remain approximate (feed.xml 97.48%, preferences.plist 97.30%). All eight authored SVG displays reach 100%, which is visible development evidence rather than unseen generalization. Long strings/comments/CDATA and closing modifiers across 512 bytes remain approximate. UTF-8 XML 1.0 is the bounded profile; no XML 1.1, custom entity expansion, DTD/schema validation, SVGZ, SVG path/CSS/JS parsing, template syntax, automatic detection or runtime parser/spelling repair is provided. Offline tools are
Existing CPython 3.12 Expat raw-event and namespace-aware validation with binary/source hashes; no downloads, SDKs or packages; no language SDK/global package is installed and collected projects
never execute. Frontend consumers require no language toolchain or Python process.

## Markdown addition

Markdown is selected model **35**. Its [verification record](markdown-browser-verification.json)
retains float32 ONNX comparisons at eight lengths, complete browser/native parity
and independent package checks.

- Chromium matches **335/335** original UTF-16 span/role/modifier references,
  including all earlier cases, eight Markdown displays and four empty/CRLF/
  Unicode/long-source probes. Markdown references include predicted-region
  composition with already registered children; these are consistency checks.
- An independent temporary Vite consumer installs four private local tarballs
  offline. Its Markdown-only build emits **one** model; Markdown + TypeScript +
  JSON emits **three**. Both builds pass **12/12** comparisons against their own
  native references, preserve original text, and exercise aliases, element/tokens
  APIs, six preset/mode pairs, heading CSS overrides and nested modifier styles.
  No repository aliases, Python provider, parser, new server or port is used.
- Playground adds a verified pinned Devicon icon, eight examples, source switching
  and light/dark styles. Full `make check` passes **175** frontend tests and all
  earlier language checks, including **14** new teacher checks against **48**
  hand-marked Golden cases. All **71** prior weight files remain preserved:
  69 retain their paths and both v1 Markdown artifacts have dated archives.

The optimized Markdown model reaches **95.10%** exact-span F1 on **20 new
independent real documents**. The unchanged 14-file exposed v1 regression improves
from **77.24% to 95.99%** and is reported separately. Eight visible displays
aggregate **95.65%**, strict neural Golden agreement is **21/48**, and visible
code-body/info predictions match **7/7** original top-level bodies.
The 894,227-parameter backbone is unchanged; an optional train-fitted joint
BIO/role decoder consumes the same neural logits in browser and Python.
Other packs retain their historical greedy decoder.
These base/region metrics do not establish complete
child semantic accuracy. [Evaluation](../packs/markdown/model/BENCHMARKS.md) and
[known limits](../packs/markdown/model/KNOWN_ISSUES.md) preserve long prose,
heading, nested-formatting and fenced-body errors. No further training follows
the first test.

Composition uses only model-predicted delimiters/info/body spans and explicit
registered IDs. Unknown/unregistered/recursive Markdown regions remain code;
container/indented code, front matter and raw HTML stay opaque. No runtime source
parser, regex repair, language guessing, code execution, Markdown document
rendering or MDX support is claimed. Existing parse-only Prettier/remark assets
remain offline with source/binary hashes; no new SDK/parser is installed.

## Dockerfile addition

Model 36 adds Dockerfile/Containerfile with one standalone ONNX asset. It learns
instructions, directives, stages/bindings, flags, Shell/JSON forms, continuations
and heredocs from offline supervision. Browser consumers do not load Go,
BuildKit, Python, a Docker service or nested Shell/JSON models. Aliases and
filenames use explicit language selection; Docker Compose stays YAML.

The [verification record](dockerfile-browser-verification.json) retains eight
numeric export lengths, 348 exact browser/native cases (all 335 prior cases,
eight Dockerfile displays, four edge probes and Markdown/Dockerfile reuse), and
an independent private-tarball consumer with public imports. That consumer emits
one model and checks 12 cases, original text/XSS escaping, aliases, element/token
APIs, six theme/mode palettes and CSS overrides. No new app, server or port is
introduced. All 73 previous weight files remain byte-identical.

First independent real-source F1 is **96.33% on 14 documents**. Validation is
**88.00% on 12 different documents**, authored test **91.96% on 120 tasks**,
eight visible displays **96.62%**, and strict neural Golden **23/42** whole cases
exact including modifiers. These are distinct evidence sets, not guarantees for
every project or platform. Two visible opaque English/Unicode heredoc bodies are
complete; Unicode comments and long/distant context remain weaker. See
[evaluation](../packs/dockerfile/model/BENCHMARKS.md) and
[known limits](../packs/dockerfile/model/KNOWN_ISSUES.md). Training stops before
the first independent adaptive test; no runtime parser/regex/spelling repair is
provided. Canonical touching-string union preserves roles and bridges no gaps.

## Makefile addition

Model 37 adds common GNU Make source as one standalone ONNX asset. It learns
targets/prerequisites, assignment/automatic/substitution variables, built-in
functions, directives/conditionals, opaque define values and common Shell
recipes, with dollar escaping, continuations and literal recipe prefixes.
Browser consumers do not run Make, Tree-sitter, Bash, Python or a nested Shell
model. Filenames and aliases use explicit language selection.

The [verification record](makefile-browser-verification.json) retains float32
comparisons at eight lengths, **361/361** browser/native cases (all 348 earlier
cases, eight displays, four edge probes and Markdown/Makefile reuse), plus an
independent private-tarball consumer. That consumer emits one model and checks
12 cases, original text/HTML escaping, aliases, element/token APIs, six theme/mode
palettes and custom CSS. The existing Playground/server/port is reused; no new
app or Python bridge is introduced. All 75 prior weight files remain unchanged.

First independent natural F1 is **89.14% on 17 files**; natural validation is
**86.94% on 11 files**, authored focus test **98.59% on 120 tasks**, and eight
visible displays **95.54%**. Strict neural Golden is **29/46** whole cases exact
including modifiers. Define bodies, long quoted commands and nested references
remain weaker. These distinct evidence sets do not guarantee complete semantic
accuracy. See [evaluation](../packs/makefile/model/BENCHMARKS.md) and
[known limits](../packs/makefile/model/KNOWN_ISSUES.md).

The offline pinned grammar and existing Bash teacher provide source-only
supervision; no collected Makefile, recipe, expansion or included file executes.
Actual validation exposed adjacent assignment tokenization, corrected before any
test under a new bound data/run revision. Original bytes/families and all old
experiments remain retained. Structural-copy exclusions stay unchanged. Inference
uses only neural predictions and source-blind touching-string union; no parser,
regex, spelling repair or whitespace-gap bridging is added.

The default complete regression currently stops at two unchanged historical Go
corpus tests, `TestFocusedCorpusReplay` and `TestModulePipelineOffline`: they
require exactly Go 1.27.1, while this host has 1.27.4. No older SDK is installed
and no version protection is changed. The available-suite run uses the local Go
and excludes only those two environment-blocked tests; all other checks run.
The verification record distinguishes that result from a complete default pass.
