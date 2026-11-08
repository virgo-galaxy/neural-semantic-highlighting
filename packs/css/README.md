# CSS family pack

One semantic pack and one shared neural model for CSS and SCSS. The document kinds
remain separate so data coverage and evaluation can be inspected for each syntax.
The existing TypeScript-family and Go packs are independent and unchanged.

## Scope

- `css`: original CSS source, including selectors, declarations, custom
  properties, functions, at-rules, queries, nesting, comments, and strings.
- `scss`: CSS-compatible source plus Sass variables, parameters, mixin/function
  declarations and calls, module references, directives, and interpolation.
- Indented `.sass` syntax, Less, Stylus, and embedded style sections are outside
  this initial pack. A source extension is not evidence of equal measured quality.

See [SEMANTICS.md](SEMANTICS.md) for exact local roles and span boundaries.
Gold describes the original source; Sass compilation must not replace it.

## Engineering boundaries

| Location | Contents | Git |
| --- | --- | --- |
| `packs/css/` | Manifest, schema, semantic contract, offline Gold tools, fixtures, runtime, selected model | Tracked |
| `training/css/` | Preparation, training, inference, evaluation, export and tests | Tracked |
| `~/Datasets/neural-semantic-highlighting/css/` | Corpus manifests, original source, Gold, statistics and prepared snapshots | External |
| `artifacts/css/<run>/` | Historical experiments, reports, resumable `best.pt` / `last.pt` | Ignored |
| `packs/css/model/` | Reviewed inference artifact and its identity, reports and known issues | Tracked |

`NSH_DATASET_ROOT` overrides the common dataset parent, just as for TS and Go.
The collector must not read or modify the adjacent Virgo Design checkout.
Use existing local source corpora first; any new sources must be explicitly
selected, versioned and recorded rather than discovered by an unrestricted crawler.

The model baseline follows the existing family: 512 UTF-8 bytes, four Transformer
layers, width 128, four attention heads, FFN 512, BIO/type/modifier heads.
Public results use UTF-16 offsets and the shared `SemanticPack` contract.
Parsers and scanners are offline Gold tools, never runtime inference dependencies.

## Development sequence

1. Freeze semantic roles and independently reviewed Golden expectations.
2. Validate offline labels, Unicode/CRLF offsets and source coverage.
3. Prepare immutable, fingerprinted data with grouping before window construction;
   keep focused cases and final test evidence separate from optimization.
4. Verify the training/checkpoint/inference path with a bounded smoke run.
5. Train and inspect validation plus real-source examples before selecting a model.

Commit each verified stage with the repository's existing short English
Conventional Commit style.

Long training runs should use a separate local process with `caffeinate -i`,
durable logs and checkpoints. Report an estimated time range and a suggested time
to return for a manual check. Do not configure scheduled monitoring or notifications.

## Status

The CSS/SCSS pack is under development. No CSS model has been selected yet.
Golden correctness and a successful smoke run do not establish trained-model
quality. Existing Playground models remain the selected TypeScript and Go artifacts.
The repository remains private.
