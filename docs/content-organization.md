# Content organization

The highlighter supports two content categories: **Code languages** (`code`) and
**File formats** (`formats`). They describe usage, not model boundaries or
installation packages. Natural-language sentence analysis is not implemented.

| Category       | Scope                                                                                  | Details                             |
| -------------- | -------------------------------------------------------------------------------------- | ----------------------------------- |
| Code languages | Programs, scripts, frontend source, stylesheets and queries, including SQL and GraphQL | [Code languages](code-languages.md) |
| File formats   | Data/configuration, XML/SVG and Markdown, Dockerfile/Makefile, Protobuf and Diff/Patch | [File formats](file-formats.md)     |

## One catalog, several consumers

```text
packages/core/src/catalog/
  types.ts       Content metadata contract
  code.ts        Code-language entries
  formats.ts     File-format entries
  index.ts       Categories, lookup, aliases and filename helper

packages/highlighter/src/catalog/index.ts
                 Public metadata-only re-export: @nsh/highlighter/catalog

apps/playground/src/views/highlighter/examples/
  code/<content-id>/<filename>
  formats/<content-id>/<filename>
  catalog.ts     Reads the shared catalog; adds application-owned icons/examples
```

Core owns the data so alias resolution does not depend on the browser package.
The public catalog entry imports no model descriptors, ONNX/WASM files, Worker,
Python provider or language SDK. The Playground uses it for labels/categories;
its icon assets remain application-owned. Documentation name/alias tables are
generated from this same catalog with `node scripts/update-catalog-docs.mjs`
after building packages. Measured quality tables retain their report provenance.

Each entry records its `id`, display `label`, `category`, registered `aliases`,
primary `modelId`, supported `extensions`, and optional direct model dependencies
or framework names. `fileVariants` records internal source kinds such as
`typescript-declaration`; these are not additional visible content entries.

## Names are not interchangeable everywhere

| Name                           | Purpose                               | Example                                        |
| ------------------------------ | ------------------------------------- | ---------------------------------------------- |
| Package name                   | Installation                          | `@nsh/highlighter` (still private/unpublished) |
| Model import path              | Select a concrete model descriptor    | `@nsh/highlighter/languages/typescript`        |
| Content ID or registered alias | Tell `highlight` what the input is    | `typescript` / `ts`, `javascript` / `js`       |
| Filename extension             | Metadata and explicit example routing | `.tsx`, `.d.ts`, `.mjs`                        |

The `language` API option remains compatible for both categories. Input names are
case-insensitive and only registered aliases are normalized. Unknown names stay
unsupported; `react` does not guess between JSX and TSX. JSX and TSX are distinct
content IDs sharing the TypeScript-family model. React examples live under
JavaScript/TypeScript. Flutter retains its existing named framework profile and
examples, normalizes to `dart`, and shares the Dart model. Ordinary shorthand
aliases such as `js`, `ts`, `yml` and `patch` do not become menu entries.

The filename helper is explicit metadata lookup, not automatic source-language
detection. Explicit JSONC selection allows files named `tsconfig.json`; explicit
dotenv selection allows `.env.local`. A chosen source family disambiguates
extensions such as `.h`. Existing source kinds and descriptor import paths remain
available, including the internal TypeScript module/declaration variants.

## Training and model paths

```text
packs/<model-id>/                  Contracts, fixtures and selected models
training/<model-id>/               Training and review tools
artifacts/<model-id>/<run>/        Historical runs and resumable checkpoints
~/Datasets/neural-semantic-highlighting/<model-name>/
                                  External corpora, Gold and prepared snapshots
```

The default dataset root remains
`~/Datasets/neural-semantic-highlighting`, with the existing
`NSH_DATASET_ROOT` override. Classification does not move or duplicate these
assets. Continue training from full checkpoints under `artifacts`, not exported
inference weights in `packs/*/model/model.pt`.

Playground examples moved into their two category folders without changing their
source bytes. Their logical IDs remain `<content-id>/<filename>` so reference
case identity stays stable. Active review/reference tools use the grouped paths;
historical reports keep the paths recorded when those experiments ran.

## Distribution boundary

This organization is independent of local bundling versus remotely hosted model
assets. Current selective imports already restrict the models emitted by the
consumer bundler. The default `@nsh/highlighter` entry contains no ONNX files. The optional
`@nsh/models` package owns local model descriptors and content-addressed assets;
`@nsh/highlighter/bundled` explicitly opts into all local models. Compatibility
`@nsh/highlighter/languages/*` paths require the optional resource package.
Remote model loading remains separate follow-up work.
Themes, custom CSS, browser inference and shared model dependencies work as before.
