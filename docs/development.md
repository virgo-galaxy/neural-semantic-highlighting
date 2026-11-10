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
