# HTML pack

One `html` entry for modern HTML documents and fragments. The source contract
follows the WHATWG HTML Living Standard; explicitly obsolete features are not a
training priority. Common and uncommon current elements, custom elements, SVG,
MathML, templates, comments, entities and attribute forms remain in scope.

Development follows the existing pack sequence: semantic contract, independent
Golden expectations, offline Gold, immutable grouped data, bounded smoke, short
training, real-source inspection, independent test, reviewed model and Playground.
Use short English Conventional Commits after each verified stage.

| Location                                        | Contents                                                                        |
| ----------------------------------------------- | ------------------------------------------------------------------------------- |
| `packs/html/`                                   | Manifest, schema, contract, offline labeling, fixtures, runtime, selected model |
| `training/html/`                                | Preparation, neural training, evaluation and diagnostics                        |
| `~/Datasets/neural-semantic-highlighting/html/` | Original source, Gold and immutable prepared snapshots; outside Git             |
| `artifacts/html/<run>/`                         | Logs, reports and full resumable training checkpoints; ignored                  |
| `packs/html/model/`                             | Reviewed inference-only model, identity and reports; tracked                    |

Reuse the shared dataset parent via `NSH_DATASET_ROOT`. Preserve all existing
language data/checkpoints/models. Do not modify Virgo Design or publish the repo.
Initialization/continuation uses full checkpoints under `artifacts`, never selected
`packs/*/model/model.pt` inference artifacts.

Stage one learns markup plus explicit script/style body roles. Later composition
can invoke existing JS/CSS neural models inside predicted regions, with the
original UTF-16 offsets restored. Attribute snippets need their own evaluation.
Tailwind class strings are ordinary attribute values initially; deeper Tailwind
coloring is a separate enhancement shared with JSX/TSX and other carriers.

See [SEMANTICS.md](SEMANTICS.md). No HTML model is selected yet. A successful
Gold or smoke test is not a mixed-language model-quality claim.
