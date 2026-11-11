# Development

Frontend usage is documented in the [root README](../README.md).

## Workspace

| Location                    | Responsibility                                              |
| --------------------------- | ----------------------------------------------------------- |
| `packages/highlighter`      | Consumer API, language descriptors and bundled models       |
| `packages/core`             | Pack registry, result contracts and HTML/Vue composition    |
| `packages/runtimes/browser` | Worker, WASM inference, cursor and decoding                 |
| `packages/renderers/html`   | Escaped HTML, full blocks and fragments                     |
| `packages/themes`           | Validated theme JSON, CSS generation and language overrides |
| `packages/runtimes/local`   | Development/native process adapter                          |
| `apps/playground`           | Vue consumer; uses browser inference                        |
| `packs/<name>`              | Manifests, offline Gold tools, selected models and reports  |
| `training/<name>`           | Training/evaluation tools                                   |
| `training/browser`          | Export and native parity tools                              |

`SemanticPack` accepts `{ source, documentKind }` and asynchronously returns a
`HighlightResult`. Spans have inclusive `start`, exclusive `end`, a `tokenType`
and optional modifiers. Selected runtimes return original UTF-16 offsets. This
contract remains independent of models, rendering, themes and transport.

HTML/Vue composition lives in Core so browser and native runtimes share it. It
uses the model's predicted regions and existing JS/TS/CSS packs. Inference never
executes source or invokes a compiler/parser/SDK.

## Checks and builds

```bash
pnpm install
pnpm dev             # Browser Playground, port 3000; no Python process
pnpm build           # Packages and production Playground
pnpm all             # Build, typecheck, lint, formatting and TypeScript tests
make check           # Also checks Python compilation/imports
pnpm pack:browser    # Local npm tarballs; does not publish
```

`pnpm clean` removes only generated `dist` folders. Packages remain private and
unpublished. Before any public release, review package naming, licenses, included
files and distribution. Making the GitHub repository public is a separate action.

## Native reference runtime

Python remains useful for training, evaluation and comparison. The old Vite
provider and local adapter are retained as development tools; the Playground no
longer registers that HTTP bridge.

```bash
.venv/bin/python -m packs.typescript.runtime.local \
  --text 'const value = 1;'
```

Persistent native providers use newline-delimited JSON over stdin/stdout, adapted
by `@nsh/local`. Their protocol carries a request ID, original source and document
kind, then returns the same ID with semantic spans or an error. This is not a
frontend installation requirement.

## Data, training and models

- External datasets: `/Users/mystic/Datasets/neural-semantic-highlighting`, or the
  configured `NSH_DATASET_ROOT`, partitioned by the existing pack names.
- Full training checkpoints and historical experiments: local `artifacts/<name>/`.
- Selected formal inference artifacts: `packs/<name>/model/`.
- Browser exports of the same selected weights: `packs/<name>/browser/`.

**Resume training from full checkpoints in `artifacts/`. Never resume from
`packs/*/model/model.pt` or a browser ONNX export.** Preserve prior experiments and
selected artifacts when evaluating candidates.

The models use byte inputs and a 512-byte context, with predicted adaptive cursor
inference over longer documents. Existing small Transformers have roughly
0.89 million parameters; 512 is the byte context, not the parameter count.

The root Makefile retains each language's data, smoke training, continuation,
evaluation, challenge and promotion commands. Follow its language-specific
variables and each `training/<name>/README.md`. For example:

```bash
make train-typescript
make continue-typescript
make evaluate-typescript
make benchmark-typescript
make challenge-regexp-typescript
```

Offline Gold environments do not become inference dependencies. Keep independent
holdouts and real-source challenges; overall scores alone do not justify model
promotion. Preserve the reports and known issues under each selected model.
Browser conversion and parity are documented [here](../training/browser/README.md).

## Theme development

Source configuration is in `packages/themes/web/src/themes/<id>/`: metadata,
complete light/dark palettes and sparse language patches. `src/schema.json`
defines the accepted roles and styles. `pnpm build` validates and generates CSS
before highlighter assets and the Playground are built.

The highlighter exposes `themes.css`, per-preset `themes/<id>.css`, and a `themes`
metadata catalog. Its existing `theme.css` remains the Default entry. The
Playground consumes these workspace exports; theme changes update CSS attributes
without changing inference or requiring a Python environment.

`SemanticSpan.documentKind` optionally preserves the language of composed child
spans. The renderer emits `data-nsh-language`; outer `data-language` remains the
document kind. Offsets/types/modifiers are unchanged. This prevents an HTML/Vue
wrapper from applying its own accents to an embedded CSS/JS/TS region.

See [the theme package guide](../packages/themes/web/README.md) for merge rules,
compatibility entries and custom CSS precedence.

## Java development

Java follows the shared standalone-pack commands and external dataset/run
locations. The offline Gold teacher uses the available OpenJDK 22.0.1 scanner and
parse-only AST with annotation processing disabled. Set `NSH_JAVA_HOME` to that JDK
when it is not the macOS Java home. This is a development dependency; browser
consumers and Playground inference do not invoke it. See
[Java training](../training/java/README.md) and the
[semantic contract](../packs/java/SEMANTICS.md) for scope and reproducible commands.

## C# development

C# keeps the shared standalone workflow and data/checkpoint locations.
`make dataset-csharp-tools` builds fixed official parser sources into project cache
using the existing native compiler. No .NET SDK, Mono or global dependency is
installed. This parser is used only for offline Gold, not by local neural inference
or the browser. See [training](../training/csharp/README.md) and the
[semantic contract](../packs/csharp/SEMANTICS.md) for scope and pinned provenance.

## C offline workflow

The C pack uses the existing Apple Clang/system C SDK; no compiler or global
package is installed. `make dataset-c-tools` builds a pinned offline grammar in
project cache. `make dataset-c` preserves captured `.c`/C `.h` bytes, complete
licenses, source hashes and quarantines, then prepares frozen source-family splits.
It never executes collected source, follows headers or expands macros.

Use [the C training commands](../training/c/README.md), initialize only from full
training checkpoints under `artifacts`, and inspect natural validation and Golden
before freezing the first adaptive test. [Scope](../packs/c/SEMANTICS.md) and
[measured limits](../packs/c/model/KNOWN_ISSUES.md) remain explicit. Frontend
consumers use `language: "c"` or `@nsh/highlighter/languages/c`; browser inference
requires no compiler, SDK, Python process or grammar.

## C++ offline workflow

The existing Apple Clang 21 / macOS SDK compiles authored C++17/20/23 option
probes and C++20 display examples. No compiler, SDK or global package is installed.
`make dataset-cpp-tools` builds fixed official grammar sources into ignored cache;
`make dataset-cpp` captures pinned original bytes/licenses, labels syntax/local
scopes, quarantines unsupported code and prepares audited frozen source families.
Collected projects never run and includes/macros are not followed or expanded.

Use [C++ training](../training/cpp/README.md) and only complete `artifacts`
checkpoints for transfer/resumption. The [report](../packs/cpp/model/BENCHMARKS.md)
records all short experiments, the family/copy audit, natural/focus evidence and
known limits. Frontends use `cpp` / `c++` / `cxx`, or selectively import
`@nsh/highlighter/languages/cpp`; no Python provider or compiler is involved.
C++ header text uses explicit `cpp`; existing `.h` mapping remains C.

## PHP offline workflow

The host has no `php` on PATH. No PHP interpreter, SDK, Composer, server or global
package is installed for this pack. `make dataset-php-tools` builds fixed official
parser sources into ignored cache using the existing native compiler; the two
entry points accept tagged PHP and tagless code without executing either.
`make dataset-php` captures pinned bytes/licenses, quarantines unsupported Blade
files and prepares copy-audited frozen source/task families.

Follow [PHP training](../training/php/README.md), use only complete `artifacts`
checkpoints and inspect real code before first test. The [report](../packs/php/model/BENCHMARKS.md)
keeps natural/focus/base/composed evidence and full experiment provenance.
`createCompositePhpPack` delegates only PHP-predicted HTML regions to existing
HTML/JS/CSS models; offline `composePhpGold` is a diagnostic, never a runtime
region selector. Frontends use `php` or `@nsh/highlighter/languages/php` without
any local Python/PHP environment. Fragmented attributes and framework template
languages remain explicit scope limits.

## Svelte offline workflow

The existing Node runtime loads one pinned official Svelte compiler bundle from
ignored project cache. No Svelte npm dependency, global tool, SDK or preprocessor
is installed. `make dataset-svelte-tools` verifies the official archive and
original license; `make dataset-svelte` captures bounded component sources,
generates original tasks and prepares immutable audited Gold/split snapshots.
The compiler only parses. Its style callback preserves UTF-16 length/newlines
while masking style bodies, so SCSS/Less require no installed preprocessor.

Use [Svelte training](../training/svelte/README.md), full `artifacts` checkpoints
and short measured stages. The [evaluation](../packs/svelte/model/BENCHMARKS.md)
records the initial and boundary revisions, all preserved source-family splits,
first held-out test and separate composed evidence. The natural holdout is small;
its score must not be replaced with the higher combined score.

`createCompositeSveltePack` delegates only predicted JS/TS/style/expression regions;
`composeSvelteGold` builds independent offline references and never chooses runtime
cuts. Frontends use `svelte` / `@nsh/highlighter/languages/svelte` through the existing
worker. Playground examples are raw source, not an installed or executed Svelte app.

## Rust offline workflow

The existing stable toolchain was updated with `rustup update stable` at the
user's request: Rust/Cargo 1.99.1 and rustup 1.29.3. Small authored standard-library
probes use `rustc --emit=metadata` for 2018/2021/2024 coverage; no collected project,
Cargo build script, dependency or procedural macro is built/executed.

`make dataset-rust-tools` builds pinned Tree-sitter sources with existing Clang in
ignored project cache. `make dataset-rust` captures bounded source/license hashes,
generates original tasks, labels original UTF-16 and freezes copy-audited families.
The Gold teacher is parse-only/source-local, not rustc type-checker output. See
[Rust training](../training/rust/README.md) and [the contract](../packs/rust/SEMANTICS.md).

Transfer/resume only full `artifacts` checkpoints. Inspect actual validation,
Golden and authored source before first test; keep natural/focus/visible scores
separate. The [evaluation](../packs/rust/model/BENCHMARKS.md) retains the initial
and literal revisions, compiler evidence and controlled raw/format-string limits.
Frontends use `rust` / `rs` or `@nsh/highlighter/languages/rust` through the existing
browser worker, without Rust/Cargo/Python or runtime syntax repair.

## Zig offline workflow

The existing host Zig was upgraded from 0.14.1 to **0.17.1** at the user's request.
This pack targets only that current release. The update includes required
LLVM/LLD dependencies and a Homebrew update; LLVM postinstall completes, and the
old Zig keg is preserved. See the [toolchain evidence](../packs/zig/model/reports/toolchain.json).
No historical-release or master corpus is mixed in.

`make dataset-zig-tools` builds a parse-only helper from that exact SDK's official
`std.zig.Ast`, `Tokenizer` and primitive metadata. SDK/compiler/helper/binary hashes
are locked in ignored project cache. `zig ast-check` performs source-only checks;
labeling never follows imports, embeds files, evaluates comptime or builds input
projects. Only authored probes, 42 task family representatives and eight display
examples are compiler-checked. No third-party parser installation is needed.

`make dataset-zig` captures original source/license hashes, freezes intact module
and task families before windows, labels and validates original UTF-16 coverage,
audits copies and prepares immutable external snapshots. Data stays under
`~/Datasets/neural-semantic-highlighting/zig`; full optimizer/RNG checkpoints and
logs under `artifacts/zig`. Review actual validation source and independent
Golden/display cases, then freeze before the first adaptive test. Resume only
full run checkpoints, never `packs/zig/model/model.pt` or ONNX. Preserve all prior
source snapshots, experiments and models. See [Zig training](../training/zig/README.md),
[contract](../packs/zig/SEMANTICS.md) and [evaluation](../packs/zig/model/BENCHMARKS.md).
Frontends use `zig` / `@nsh/highlighter/languages/zig` through the existing browser
worker and need no SDK, Python provider or runtime syntax repair.

## Dart offline workflow

No Dart/Flutter SDK, analyzer, pub environment or global dependency is installed.
The pinned independent Tree-sitter 0.25.10 / Dart grammar 0.3.0 uses existing
Apple Clang to build a project-local parse-only library. Parser sources, Git blobs,
licenses, compiler identity and library hashes are locked in ignored cache.
This provides CST/source-local Gold rather than official analyzer semantics.
Imports, annotations, generators and input projects never execute.

`make dataset-dart` captures 212 bounded official Dart-package/Flutter-stable
sources with original licenses, generates 55 original task families and eight
literal/context families, labels/validates original UTF-16, audits cross-family
copies and prepares immutable external snapshots. All 94 initial assignments
remain; the final frozen map extends to 102 before corrected training. Golden and
Playground are excluded. Eleven teacher tests and 35 manually marked cases are
separate from neural scores. Display examples have parse/coverage evidence only,
without SDK/compiler checks.

Data stays under `~/Datasets/neural-semantic-highlighting/dart`; full resumable
optimizer/RNG checkpoints, candidate archives and measured run logs under
`artifacts/dart`. Review actual validation source and visible probes before
freezing and the first adaptive test; preserve all previous data/runs/models.
Initialize/resume only full checkpoints, never inference `.pt`/ONNX. See
[Dart training](../training/dart/README.md), [contract](../packs/dart/SEMANTICS.md)
and [evaluation](../packs/dart/model/BENCHMARKS.md). Frontends use `dart` or
`@nsh/highlighter/languages/dart` through the existing browser worker. Flutter
source shares that model without an installed framework or widget resolution.

## Flutter coverage within Dart

Flutter is a public alias and dedicated Playground group sharing the unchanged
Dart descriptor, weights, schema and `.dart` file mapping. The Flutter selective
entry re-exports Dart; it adds no separate model pack or model asset. There is no
Dart/Flutter SDK, analyzer, pub environment, generator or source execution.

`make dataset-flutter-examples` captures 48 pinned application sources/licenses
under the existing external Dart dataset root. `make evaluate-flutter` reviews
those files and audits exact/lexical/shape matches against prior Gold;
`make challenge-flutter` reviews eight hand-marked probes and eight displayed
examples. Both use `DART_DEVICE`, with output paths configurable through
`FLUTTER_REPORT` and `FLUTTER_CHALLENGE_REPORT`. These review files are excluded
from training and do not replace the historical Dart held-out test. Existing
source-family assignments, checkpoints, models and reports remain preserved.

The [Flutter report](../packs/dart/model/FLUTTER.md) records the measured decision
to reuse the current weights, including strict Golden and source-local limits.
The public alias canonicalizes to Dart; the Playground keeps its own Flutter
label/icon while `.dart` sources are routed to Dart inference.

## Swift offline workflow

Swift follows the shared command names and existing external dataset/checkpoint
locations. The already installed official Swift 6.4.2 SwiftParser supplies offline
source-accurate Gold, without typechecking, loading project dependencies, expanding
macros or executing collected code. Offline supervision installs no SDK or language package.
`make dataset-swift` preserves pinned original source/license blobs, immutable
snapshots, copy audits and frozen source families. `make test-labeling-swift` checks
28 independent Golden cases and 12 focused tests.

See [Swift training](../training/swift/README.md), [semantic scope](../packs/swift/SEMANTICS.md)
and [the selected model](../packs/swift/model/BENCHMARKS.md). Resume full artifacts
checkpoints, never model.pt/ONNX; preserve every prior language's formal weights.
Six authored examples typecheck on 6.4.2; two common SwiftUI examples additionally
typecheck with preserved Xcode Swift 6.0.3/macOS 15.2 SDK because the current CLI
SDK's SwiftUIMacros plugin is absent. No SDK/plugin installation is attempted.
This is offline validation only: consumer and Playground inference are browser
native and need no compiler, parser, Python provider or new application/port.

## Kotlin offline workflow

Kotlin follows the shared command names and external dataset/checkpoint locations.
`make dataset-kotlin-tools` prepares pinned official Kotlin 2.4.21 Maven JARs only
in ignored project cache, reusing the existing JDK 22.0.1. It installs no Kotlin
SDK, Gradle, Android SDK or global language dependency. Offline PSI/lexer Gold
never executes source/scripts, resolves dependencies or loads compiler plugins.

`make dataset-kotlin` retains original pinned blobs/licenses, immutable snapshots,
copy audits and frozen source families. The original curriculum stays unchanged;
a separate mixed generator adds 288 independent tasks after literal/role review.
`make test-labeling-kotlin` checks 13 tests and 32 manually marked Golden cases.
Six authored JVM examples also compile using the cached official compiler and
libraries; Compose and Gradle examples are parse-only. None executes.

See [training](../training/kotlin/README.md), [semantic scope](../packs/kotlin/SEMANTICS.md)
and [selected evaluation](../packs/kotlin/model/BENCHMARKS.md). Resume full artifacts
checkpoints only; inference .pt/ONNX files are never resumable. Frontend inference
uses the existing browser worker without JVM, Kotlin, parser or Python.

## R offline workflow

`make dataset-r` follows the existing external dataset/checkpoint paths,
immutable revisions, copy audits and frozen source families. `make dataset-r-tools`
prepares r-lib tree-sitter-r 1.3.0 and Tree-sitter 0.25.10, compiled with existing Clang only in project cache. No language SDK or global package is installed; collected
source, dependencies and projects never execute. `make test-labeling-r` checks
10 tests and 32 independently hand-marked Golden cases.
See [training](../training/r/README.md), [semantic scope](../packs/r/SEMANTICS.md)
and [selected evaluation](../packs/r/model/BENCHMARKS.md). Resume full artifacts
checkpoints only; inference .pt/ONNX files never resume training. Frontend and
Playground inference uses the existing browser worker without a Python bridge.

## Scala offline workflow

`make dataset-scala` follows the existing external dataset/checkpoint paths,
immutable revisions, copy audits and frozen source families. `make dataset-scala-tools`
prepares Tree-sitter Scala 0.26.12 with runtime 0.25.10, compiled with existing Clang only in project cache. No language SDK or global package is installed; collected
source, dependencies and projects never execute. `make test-labeling-scala` checks
13 tests and 33 independently hand-marked Golden cases.
See [training](../training/scala/README.md), [semantic scope](../packs/scala/SEMANTICS.md)
and [selected evaluation](../packs/scala/model/BENCHMARKS.md). Resume full artifacts
checkpoints only; inference .pt/ONNX files never resume training. Frontend and
Playground inference uses the existing browser worker without a Python bridge.

## Ruby offline workflow

`make dataset-ruby` follows the existing external dataset/checkpoint paths,
immutable revisions, copy audits and frozen source families. `make dataset-ruby-tools`
prepares Tree-sitter Ruby 0.23.1 at ad907a69 with runtime 0.25.10, compiled with existing Clang only in project cache. No language SDK or global package is installed; collected
source, dependencies and projects never execute. `make test-labeling-ruby` checks
13 tests and 33 independently hand-marked Golden cases.
See [training](../training/ruby/README.md), [semantic scope](../packs/ruby/SEMANTICS.md)
and [selected evaluation](../packs/ruby/model/BENCHMARKS.md). Resume full artifacts
checkpoints only; inference .pt/ONNX files never resume training. Frontend and
Playground inference uses the existing browser worker without a Python bridge.

## Lua offline workflow

`make dataset-lua` follows the existing external dataset/checkpoint paths,
immutable revisions, copy audits and frozen source families. `make dataset-lua-tools`
prepares Tree-sitter Lua 0.5.0 at 10fe0054 with runtime 0.25.10, compiled with existing Clang only in project cache. No language SDK or global package is installed; collected
source, dependencies and projects never execute. `make test-labeling-lua` checks
13 tests and 32 independently hand-marked Golden cases.
See [training](../training/lua/README.md), [semantic scope](../packs/lua/SEMANTICS.md)
and [selected evaluation](../packs/lua/model/BENCHMARKS.md). Resume full artifacts
checkpoints only; inference .pt/ONNX files never resume training. Frontend and
Playground inference uses the existing browser worker without a Python bridge.
