# Optional local model assets

`@nsh/models` contains the selected, unmodified ONNX models and their pinned
metadata. It is a private workspace package, not yet published on npm.
The highlighter's default entry does not import or require this package.

Import only the models the application uses:

```ts
import { createHighlighter } from "@nsh/highlighter";
import css from "@nsh/models/languages/css";
import typescript from "@nsh/models/languages/typescript";

const highlighter = createHighlighter({ languages: [typescript, css] });
```

The optional resource package itself contains all selected weights. Explicit
subpath imports restrict the models emitted into a consumer's production assets;
they do not make the npm resource archive a two-model archive.

For an application that deliberately bundles every model, import
`createHighlighter` from `@nsh/highlighter/bundled`. Existing
`@nsh/highlighter/languages/*` paths forward to this package for compatibility.

The build validates the model and metadata hashes against the generated catalog.
`dist/assets/` is a self-contained resource directory, with `manifest.json` and
content-addressed `v1/<model-id>/` files. Model weights, full training checkpoints
and external datasets remain at their existing locations.

For maintainers: after exporting a newly selected browser model, regenerate its
local descriptor and the pinned resource catalog before rebuilding:

```bash
python3 -m training.browser.generate_descriptors --pack typescript
```

Omit `--pack` to refresh all descriptors. Format generated TypeScript with the
repository formatter. Generation reads selected browser metadata; it does not
move datasets, rewrite weights or alter resumable checkpoints.
