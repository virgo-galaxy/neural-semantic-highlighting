# Neural Semantic Highlighting

A runtime-agnostic neural semantic highlighting engine.

## Workspace

| Location                              | Responsibility                                                                                     |
| ------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `packages/core` (`@nsh/core`)         | Public contracts, pack registry, and highlighter orchestration                                     |
| `packages/html` (`@nsh/html`)         | Semantic spans to escaped HTML; depends on Core                                                    |
| `packages/themes` (`@nsh/themes`)     | CSS assets: base palette, language overrides, and default entry                                    |
| `apps/playground` (`@nsh/playground`) | Vue 3 + Vite application using the workspace packages                                              |
| `packs/typescript`                    | Manifest, schema, semantic contract, labeling/data tools, fixtures, challenges, and selected model |
| `training/typescript`                 | Python training, prediction, evaluation, and diagnostics                                           |
| `tests`                               | Shared package and TypeScript pack regression tests                                                |
| `artifacts`                           | Local experimental checkpoints and reports; not a runtime package                                  |

The root is a private workspace coordinator, not a library entry point. All workspace packages remain private until distribution and licensing are reviewed. The package names above are local workspace identifiers, not a claim that those names have been published or reserved on npm.

## Development

Run commands from the repository root:

```bash
pnpm install
make check
pnpm dev
```

`pnpm dev` builds the library packages and starts the Playground on `http://127.0.0.1:4173/`. Stop that process with Ctrl+C. No global installation or `npm link`/`pnpm link` is required. Local workspace dependencies use `workspace:*`.

The Playground still uses the existing deterministic demonstration pack. This migration does not add neural inference or a model server.

## Packages and build

- `pnpm build`: builds workspace projects in dependency order, including the Playground.
- `pnpm build:packages`: builds library packages only.
- `pnpm typecheck`: builds fresh library declarations and typechecks the shared tests and pack tools.
- `pnpm test`: builds fresh library output before running the tests against package entry points.
- `pnpm clean`: removes package/application `dist` directories only; it does not remove models or training artifacts.
- `make check`: builds, typechecks, lints, checks formatting, runs the TypeScript tests, and checks Python compilation/imports.

Core and HTML emit JavaScript and declarations in their own `dist` directories. Themes ships CSS directly without a copy/build step. Consumers with a CSS-aware build tool can import:

```ts
import "@nsh/themes/default.css";

import { createHighlighter } from "@nsh/core";
import { renderToHtml } from "@nsh/html";
```

Cross-package imports use package names. Relative `.js` imports remain valid inside each package. Core does not depend on HTML, CSS, a UI framework, Python, or a model artifact.

## TypeScript model and training

The selected inference artifact and its documentation remain in [`packs/typescript/model`](packs/typescript/model/README.md). Its files and evaluation reports are unchanged by this migration.

Current TypeScript neural runtime:

- Context: 512 UTF-8 bytes.
- Training windows: adaptive semantic cursor using Gold span boundaries.
- Inference windows: adaptive predicted cursor.
- No fixed overlap percentage or overlap fusion in the default runtime.
- RegExp: focused curriculum with halo and operator-slash negatives.
- Experiment directory: `artifacts/typescript/context512-re`.
- Training data: external, defaulting to `~/Datasets/neural-semantic-highlighting`.
- Existing training and evaluation commands remain in the unchanged `Makefile`.

Do not pass the selected inference artifact to `train.py --resume`; use the original training checkpoint for continuation.
