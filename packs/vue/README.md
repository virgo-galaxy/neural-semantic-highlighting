# Vue pack

One `vue` document kind for `.vue` single-file components across Vue 2, Vue 3
Options/Composition API and Vue 3.2 `script setup`. Version-specific development
probes and real-source groups are evaluated separately; one successful version
does not establish the others.

Reuse existing neural JS/TS/JSX/TSX and CSS/SCSS/Less packs for code bodies. A small
Vue markup/region model learns template syntax and embedded boundaries, initialized
weights-only from a full HTML training checkpoint under `artifacts`. Existing
formal models remain unchanged. Parsers are offline Gold tools only.

Follow the established sequence: contract, independent Golden fixtures, offline
Gold, immutable directory-grouped data, smoke, short training, source inspection,
independent test, reviewed inference bundle and Playground. Keep short English
Conventional Commits after verified stages. Preserve every previous experiment.

| Location                                       | Contents                                                                |
| ---------------------------------------------- | ----------------------------------------------------------------------- |
| `packs/vue/`                                   | Contract, schema, Gold, fixtures, runtime and reviewed model            |
| `training/vue/`                                | Data preparation, short training and independent evaluation             |
| `~/Datasets/neural-semantic-highlighting/vue/` | Frozen sources, Gold, prepared tensors and source licenses; outside Git |
| `artifacts/vue/<run>/`                         | Logs, reports and full resumable checkpoints; ignored                   |

Use `NSH_DATASET_ROOT` for the shared external parent. Resume only full `last.pt`
checkpoints, never `packs/*/model/model.pt`. This project remains private and
independent of Virgo Design. See [SEMANTICS.md](SEMANTICS.md).

No Vue inference model is selected yet.
