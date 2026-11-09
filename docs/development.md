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
