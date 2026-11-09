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
