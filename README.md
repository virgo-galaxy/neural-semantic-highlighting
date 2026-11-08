# Neural Semantic Highlighting

A runtime-agnostic neural semantic highlighting engine.

NSH separates semantic inference from rendering. A semantic pack receives source code and returns theme-independent semantic spans; consumers decide how those spans are rendered and styled.

## Supported languages and formats

All entries below have selected models, local inference and Playground examples.
They currently run through the local Python process bridge; native browser
inference is not implemented.

The reported metric is **exact-span F1**: a prediction must match a token's start,
end and semantic type. It is not character accuracy or the percentage of files
highlighted perfectly. Natural-source test results are shown where available;
JS/TS uses its archived combined test. Different datasets and sample sizes are
not directly comparable. Each linked report records the evaluation scope and
remaining failures.

| Name                                                        | Supported source / file extensions                                                                                                                                  | Measured test exact-span F1                                                                                 | Current state / measured limits                                                                                                  |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| [JavaScript / TypeScript](packs/typescript/model/README.md) | JS/TS modules and declarations, JSX/TSX including React component source; `.js`, `.mjs`, `.cjs`, `.jsx`, `.ts`, `.mts`, `.cts`, `.tsx`, `.d.ts`, `.d.mts`, `.d.cts` | [99.31%](packs/typescript/model/BENCHMARKS.md) — archived combined whole-document test                      | Available locally; [RegExp, comment and long-string boundaries](packs/typescript/model/KNOWN_ISSUES.md) remain limited           |
| [Go](packs/go/model/README.md)                              | Go source; `.go`                                                                                                                                                    | [99.03%](packs/go/model/README.md#selected-candidate) — natural test                                        | Available locally; [long raw strings and cross-file names](packs/go/model/KNOWN_ISSUES.md) remain limited                        |
| [CSS / SCSS / Less](packs/css/model/README.md)              | Stylesheets and preprocessor source; `.css`, `.scss`, `.less`                                                                                                       | [CSS 99.04%; SCSS 99.40%; Less 99.42%](packs/css/model/BENCHMARKS.md) — natural test, per language          | Available locally; [individual grid/token and boundary errors](packs/css/model/KNOWN_ISSUES.md) remain                           |
| [HTML](packs/html/model/README.md)                          | Modern HTML; `.html`, `.htm`; JS/CSS composition inside predicted `<script>` / `<style>` bodies                                                                     | [Markup 96.37%; composed 96.53%](packs/html/model/BENCHMARKS.md) — natural test, separate scopes            | Available locally; [comments and embedded-region boundaries](packs/html/model/KNOWN_ISSUES.md) remain limited                    |
| [Vue](packs/vue/model/README.md)                            | Vue 2 / Vue 3 / Vue 3.2 SFCs; `.vue`; existing script/style models reused                                                                                           | [97.12%](packs/vue/model/BENCHMARKS.md) — natural composed test; profile results are separate in the report | Available locally; [SFC region boundaries and sparse syntax coverage](packs/vue/model/KNOWN_ISSUES.md) remain limited            |
| [Python](packs/python/model/README.md)                      | Python 3 source and stubs; `.py`, `.pyw`, `.pyi`                                                                                                                    | [87.52%](packs/python/model/BENCHMARKS.md) — natural test                                                   | Usable local baseline; [name roles and long docstrings](packs/python/model/KNOWN_ISSUES.md) remain weaker                        |
| [Shell](packs/bash/model/README.md)                         | POSIX sh, Bash, Zsh, Csh/Tcsh; `.sh`, `.bash`, `.zsh`, `.csh`, `.tcsh`; Git Bash shares Bash syntax                                                                 | [84.78% overall; Bash 93.20%](packs/bash/model/BENCHMARKS.md) — known natural-test comparison               | Usable local baseline, Bash prioritized; [complex Zsh and Here Document endings](packs/bash/model/KNOWN_ISSUES.md) remain weaker |
| [Perl](packs/perl/model/README.md)                          | Perl 5 scripts, modules and tests; `.pl`, `.pm`, `.t`, `.perl`                                                                                                      | [83.60%](packs/perl/model/BENCHMARKS.md) — natural test                                                     | Usable local baseline; [mixed Here Documents and role/modifier boundaries](packs/perl/model/KNOWN_ISSUES.md) remain weaker       |

## Architecture

```text
Source
  ↓
SemanticPack
  ↓
HighlightResult
  ↓
Renderer
  ↓
Theme / UI
```

The `SemanticPack` contract is the runtime boundary. A pack may run a model locally, inside the browser, or behind a remote transport. NSH consumers depend only on the contract and the returned `HighlightResult`.

```ts
export interface HighlightRequest {
  source: string;
  documentKind: string;
}

export interface SemanticPack {
  manifest: PackManifest;
  highlight(request: HighlightRequest): Promise<HighlightResult>;
}
```

Possible runtime implementations include:

- local native/process runtimes;
- browser runtimes using technologies such as WASM, WebGPU, or ONNX;
- remote runtimes using transports such as HTTP.

HTTP is not part of the core protocol.

## Workspace

| Location                                 | Responsibility                                                                                  |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `packages/core` (`@nsh/core`)            | Public contracts, pack registry, and highlighter orchestration                                  |
| `packages/renderers/html` (`@nsh/html`)  | Semantic spans to escaped HTML; depends on Core                                                 |
| `packages/runtimes/local` (`@nsh/local`) | Node.js local-process `SemanticPack` adapter using newline-delimited JSON over stdin/stdout     |
| `packages/themes` (`@nsh/themes`)        | CSS assets: base palette, language overrides, and default entry                                 |
| `apps/playground` (`@nsh/playground`)    | Vue 3 + Vite Playground using the workspace packages and selected local models                  |
| `packs/typescript`                       | TypeScript/JavaScript manifest, semantic contract, tools, fixtures, runtime, and selected model |
| `training/typescript`                    | TypeScript/JavaScript Python training, prediction, evaluation, and diagnostics                  |
| `packs/go`                               | Go manifest, semantic contract, data/labeling tools, runtime, and selected model                |
| `training/go`                            | Go Python training, prediction, evaluation, export, and diagnostics                             |
| `tests`                                  | Shared package and pack regression tests                                                        |
| `packs/css`                              | CSS/SCSS/Less semantic contract, offline Gold tooling, fixtures and local neural runtime        |
| `training/css`                           | CSS-family preparation, short resumable training and per-kind evaluation                        |
| `packs/html`                             | Modern HTML contract, offline Gold, fixtures, base model and embedded JS/CSS composition        |
| `training/html`                          | HTML data preparation, short training, base/body and composed evaluation                        |
| `packs/vue`                              | Vue 2/3/3.2 SFC contract, Gold, base model and existing child-pack composition                  |
| `training/vue`                           | Versioned data preparation, short training, profile/feature and composed evaluation             |
| `artifacts`                              | Local experimental checkpoints and reports; not a runtime package                               |

The repository root is a private workspace coordinator, not a library entry point. All workspace packages remain private until distribution and licensing are reviewed. Package names are local workspace identifiers and do not imply npm publication or reservation.

## Development

Run commands from the repository root:

```bash
pnpm install
make check
pnpm dev
```

`pnpm dev` builds the library packages and starts the Playground on:

```text
http://127.0.0.1:3000/
```

The Playground Vite server configuration lives in `apps/playground/vite.config.ts`.

No global installation or `npm link` / `pnpm link` is required. Local workspace dependencies use `workspace:*`.

## Playground

The Playground runs the selected language models listed above through the normal NSH contracts.

```text
Browser Playground
  ↓
app-local Vite development bridge
  ↓
@nsh/local
  ↓
long-lived Python process over stdin/stdout
  ↓
selected pack model
  ├─ packs/typescript/model/model.pt
  ├─ packs/go/model/model.pt
  ├─ packs/css/model/model.pt
  ├─ packs/html/model/model.pt → existing JS/CSS packs inside predicted bodies
  ├─ packs/vue/model/model.pt → existing JS/TS/JSX/TSX and CSS/SCSS/Less packs
  ├─ packs/python/model/model.pt
  ├─ packs/bash/model/model.pt
  └─ packs/perl/model/model.pt
  ↓
HighlightResult
  ↓
@nsh/html
  ↓
@nsh/themes
```

The browser cannot spawn the Python model process directly, so the Playground uses a development-only Vite bridge under `/__nsh/local`. That HTTP hop exists only as browser-to-Vite transport for this web application; it does not define or constrain the `SemanticPack` contract.

The local model process is started lazily and kept alive. Model initialization is therefore paid once per process lifetime rather than once per highlight request.

The Playground currently includes:

- TypeScript, JavaScript, Go, CSS, SCSS, Less, HTML, Vue, Python, Shell and Perl source examples discovered from real files;
- editable and highlighted presentation states;
- highlighting when the code block leaves editing focus;
- preserved native undo/redo history across presentation-state changes;
- measured end-to-end highlight latency;
- light and dark themes;
- Reka UI primitives for interactive controls while NSH keeps its own visual styling.

## Packages and build

- `pnpm build`: builds workspace projects in dependency order, including the Playground.
- `pnpm build:packages`: builds library packages only.
- `pnpm typecheck`: builds fresh library declarations and typechecks the shared tests and pack tools.
- `pnpm test`: builds fresh library output before running tests against package entry points.
- `pnpm clean`: removes package/application `dist` directories only; it does not remove models or training artifacts.
- `make check`: builds, typechecks, lints, checks formatting, runs TypeScript tests, and checks Python compilation/imports.

Core, HTML, and Local emit JavaScript and declarations in their own `dist` directories. Themes ships CSS directly without a copy/build step.

Consumers with a CSS-aware build tool can import:

```ts
import "@nsh/themes/default.css";

import { createHighlighter } from "@nsh/core";
import { renderToHtml } from "@nsh/html";
```

Cross-package imports use package names. Relative `.js` imports remain valid inside each package. Core does not depend on HTML, CSS, Vue, Python, a transport, or a model artifact.

## Local process runtime

`@nsh/local` adapts one long-lived child process to the `SemanticPack` interface.

The provider protocol is newline-delimited JSON over stdin/stdout. A request contains an integer request ID, source text, and document kind. The provider returns the same request ID with either a `HighlightResult` or an error.

The selected packs provide Python implementations at:

```text
packs/typescript/runtime/local.py
packs/go/runtime/local.py
```

Both selected runtimes consume source text and neural model weights directly. The Go runtime does
not invoke the Go compiler, scanner, parser, AST, type checker, or language server.

Example:

```bash
.venv/bin/python -m packs.typescript.runtime.local \
  --text 'const value = 1;'
```

Persistent stdio mode:

```bash
printf '%s\n' \
  '{"id":1,"source":"const value = 1;","documentKind":"typescript"}' \
  '{"id":2,"source":"let re = /foo+/gi;","documentKind":"typescript"}' \
| .venv/bin/python -m packs.typescript.runtime.local --stdio
```

## Highlight result

The stable result format is theme-independent:

```ts
type OffsetEncoding = "utf-8" | "utf-16" | "utf-32";

interface SemanticSpan {
  start: number;
  end: number;
  tokenType: string;
  modifiers?: readonly string[];
}

interface HighlightResult {
  offsetEncoding: OffsetEncoding;
  spans: SemanticSpan[];
}
```

The selected TypeScript-family and Go packs return UTF-16 offsets. `start` is inclusive and `end` is exclusive.

## HTML and themes

`@nsh/html` renders semantic spans to escaped HTML with a stable semantic DOM contract:

- `.nsh`
- `.nsh-token`
- `data-language`
- `data-token-type`
- `data-modifiers`

Themes are CSS-native. Core does not know about colors or CSS. The intended cascade is:

1. base semantic palette;
2. language-specific overrides;
3. consumer or application CSS.

This keeps the semantic engine independent from any particular visual theme or UI framework.

## TypeScript model

The currently selected inference artifact and its documentation live in [`packs/typescript/model`](packs/typescript/model/README.md).

Current selected model:

| Field                     | Value                                                           |
| ------------------------- | --------------------------------------------------------------- |
| Selected checkpoint epoch | 44                                                              |
| Selection metric          | validation `exact_span_macro_f1`                                |
| Selection score           | 0.9864                                                          |
| Parameters                | 897,065                                                         |
| Context                   | 512 UTF-8 bytes, not BPE tokens                                 |
| Architecture              | Transformer encoder; 4 layers, 128 dimensions, 4 heads, FFN 512 |
| Output heads              | 3 BIO classes; 24 token types; 14 modifiers                     |
| Public span offsets       | UTF-16 code units                                               |
| Document inference        | predicted adaptive cursor, greedy decoding                      |

Whole-document test results for the selected model:

| Metric              | Value  |
| ------------------- | ------ |
| Precision           | 0.9918 |
| Recall              | 0.9943 |
| Exact-span F1       | 0.9931 |
| Exact-span macro F1 | 0.9852 |

These scores do not imply universal accuracy. The independent RegExp challenge remains materially harder, and several semantic types have limited or zero positive support in the current test split. See [`BENCHMARKS.md`](packs/typescript/model/BENCHMARKS.md) and [`KNOWN_ISSUES.md`](packs/typescript/model/KNOWN_ISSUES.md) for the measured details and limitations.

## Go model

The selected Go inference artifact and its documentation live in [`packs/go/model`](packs/go/model/README.md).

The current candidate uses a 512-byte Transformer model and pure-neural predicted-adaptive-cursor
inference. The selected runtime has no Go-toolchain dependency. The held-out natural test measured
`0.9903` exact-span F1 and `0.9676` macro F1; focused stress cases remain documented rather than
being hidden behind runtime heuristics.

Maintainers promote a reviewed training checkpoint with:

```bash
make export-go-model \
  GO_CHECKPOINT=artifacts/go/<run>/best.pt \
  GO_TEST_REPORT=artifacts/go/<run>/test-adaptive-<stamp>.json
```

Normal Playground startup does not require a checkpoint environment variable:

```bash
pnpm dev
```

`NSH_GO_CHECKPOINT` remains an optional development override for trying an external checkpoint
without replacing the selected artifact.

## TypeScript-family scope

The current pack declares support for:

| Document kind                     | Extensions |
| --------------------------------- | ---------- |
| `javascript`                      | `.js`      |
| `javascript-esm`                  | `.mjs`     |
| `javascript-commonjs`             | `.cjs`     |
| `jsx`                             | `.jsx`     |
| `typescript`                      | `.ts`      |
| `typescript-esm`                  | `.mts`     |
| `typescript-commonjs`             | `.cts`     |
| `tsx`                             | `.tsx`     |
| `typescript-declaration`          | `.d.ts`    |
| `typescript-esm-declaration`      | `.d.mts`   |
| `typescript-commonjs-declaration` | `.d.cts`   |

This manifest is a capability declaration, not evidence of equal measured quality for every document kind.

## Training and evaluation

Current TypeScript training defaults:

- context: 512 UTF-8 bytes;
- batch size: 32;
- training windows: adaptive semantic cursor using Gold span boundaries;
- inference windows: adaptive predicted cursor;
- no fixed overlap percentage or overlap fusion in the default runtime;
- RegExp-focused curriculum with halo and operator-slash negatives;
- default local training-run directory: `artifacts/typescript/run`;
- training data: external, defaulting to `~/Datasets/neural-semantic-highlighting`.

Training and evaluation commands are available through the root `Makefile`. The selected TypeScript model metadata and archived reports may still mention the historical run that produced that model; those provenance records are not active training defaults.

Examples:

```bash
make train-typescript
make continue-typescript
make evaluate-typescript
make benchmark-typescript
make challenge-regexp-typescript
make challenge-regexp-paired-typescript
```

Do not pass the selected inference artifact in `packs/typescript/model/model.pt` to `train.py --resume`. Resume training from the original training checkpoint in `artifacts/`.

## Repository boundaries

- Public APIs, schemas, examples, fixtures, benchmarks, and test data should remain neutral and reusable.
- Training datasets remain outside the repository.
- Historical experiment checkpoints remain under local `artifacts/`; they are not replaced by the selected inference artifact.
- Selected models under `packs/*/model/` are formal inference artifacts and should be updated together with their identity, reports, benchmarks, and known-issues documentation.
- Runtime consumers should depend on `SemanticPack` rather than a specific model framework or transport.

## Status

NSH is currently an early-stage private project. The TypeScript-family and Go models, local process runtimes, HTML renderer, CSS themes, and Vue Playground are integrated and working together. Browser-native and remote runtime implementations remain future directions rather than current requirements.

The [CSS family pack](packs/css/README.md) adds CSS, SCSS and Less with one shared
894,227-parameter model, a local neural runtime and Playground examples. Its
[model report](packs/css/model/README.md) records held-out results and known issues.
See [training/css](training/css/README.md) for short runs, checkpoint continuation,
explicit weights-only initialization and independent adaptive evaluation.
Normal startup needs no CSS checkpoint variable; `NSH_CSS_CHECKPOINT` can select
an experimental checkpoint before running `pnpm dev`.

The [HTML pack](packs/html/README.md) adds one modern HTML entry, using an
893,711-parameter base model and existing JS/CSS models inside neurally predicted
body regions. Its [model report](packs/html/model/README.md) separates base and
composed evidence and records material raw-text/boundary limits. Explicitly obsolete
features are not training targets; current uncommon syntax stays in scope.
Tailwind classes and inline style/event attributes remain strings. See
[training/html](training/html/README.md) for data, short runs and continuation.
Normal startup needs no HTML override; `NSH_HTML_CHECKPOINT` can select an
experimental full checkpoint. Existing language models remain unchanged.

The [Vue pack](packs/vue/README.md) adds one `.vue` entry covering Vue 2,
Vue 3 Options/Composition API and Vue 3.2 script setup. Its 894,485-parameter
markup/region model reuses the HTML model implementation and a full HTML training
checkpoint for weights-only initialization. Embedded code reuses existing
JS/TS/JSX/TSX and CSS/SCSS/Less neural packs. Mustache expressions are composed;
directive values and Tailwind classes remain whole strings initially. See the
[versioned model report](packs/vue/model/README.md) and
[known issues](packs/vue/model/KNOWN_ISSUES.md). Training data stays external under
`NSH_DATASET_ROOT/vue`; full checkpoints stay in `artifacts/vue`. Start normally
with `pnpm dev`, or set `NSH_VUE_CHECKPOINT` for an experimental checkpoint.

The [Python pack](packs/python/README.md) adds one `.py`/`.pyw`/`.pyi` entry with
an independent 894,614-parameter model and the same persistent local process
bridge. The bounded first baseline covers modern Python source, with f/t-strings
kept whole. Natural held-out exact-span F1 is 87.52%; local name-role distinctions
and long docstrings remain weaker areas. See the
[benchmark](packs/python/model/BENCHMARKS.md) and
[measured limits](packs/python/model/KNOWN_ISSUES.md). Offline Gold uses a separate
pinned CPython; inference needs only the existing PyTorch environment.
`NSH_PYTHON_CHECKPOINT` can select a development checkpoint. Data stays external
under `NSH_DATASET_ROOT/python`; full checkpoints stay in `artifacts/python`.

The [Shell pack](packs/bash/README.md) adds one entry for POSIX sh, Bash, Zsh and
Csh/Tcsh, with one 893,582-parameter model and separate offline coverage profiles.
Inference needs no native shell or lexer. The
[benchmark](packs/bash/model/BENCHMARKS.md) separates focused grammar from the small
known natural test: Bash 93.20%, POSIX 88.32%, Csh 89.29%, Zsh 73.76% exact-span F1.
Complex expansion and name-role errors remain in the
[measured limits](packs/bash/model/KNOWN_ISSUES.md). Data/checkpoints follow
`NSH_DATASET_ROOT/bash` and `artifacts/bash`; `NSH_BASH_CHECKPOINT` selects a
configuration-compatible development checkpoint. Git Bash shares Bash syntax.

The Shell Here Document follow-up adds ordinary/quoted/`<<-` examples and both
`function` forms. New focused holdout tasks score 96.76% exact-span F1, versus
58.84% for the preserved previous model. Terminator overruns in short standalone
fragments remain documented; formal inference still uses no source lexer.

The [Perl pack](packs/perl/README.md) adds a Perl 5 entry with one independent
894,227-parameter model, five examples and the same local process bridge. Offline
Gold uses existing PPI without executing source; inference needs no Perl parser.
First natural/focus test F1 is 83.60%/88.21%, with bounded core-module coverage.
Read its [benchmark](packs/perl/model/BENCHMARKS.md) and
[measured limits](packs/perl/model/KNOWN_ISSUES.md), including mixed Here Documents.
Data/checkpoints follow `NSH_DATASET_ROOT/perl` and `artifacts/perl`;
`NSH_PERL_CHECKPOINT` selects a compatible development candidate.
