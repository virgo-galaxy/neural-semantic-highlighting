# Python pack

One Python entry for modern Python source, script and stub files. Reuse the
existing small Transformer, neural byte inference, semantic-span contract,
renderer and themes. The model/runtime stays independent of Python's parser;
`ast` and `tokenize` are offline Gold tools only. Source is never executed.

Follow the established workflow: semantic contract, independent Golden fixtures,
immutable grouped data, smoke/resume verification, short training, real-source
inspection, frozen independent test, reviewed model and Playground. Use short
English Conventional Commits after verified stages; preserve existing artifacts.

| Location                                          | Contents                                                                       |
| ------------------------------------------------- | ------------------------------------------------------------------------------ |
| `packs/python/`                                   | Contract, schema, offline Gold, fixtures, runtime and selected inference model |
| `training/python/`                                | Pack-specific preparation/training/evaluation entry points                     |
| `training/shared/`                                | Source-independent training primitives reused by new packs                     |
| `~/Datasets/neural-semantic-highlighting/python/` | Original source, Gold, immutable snapshots and licenses; outside Git           |
| `artifacts/python/<run>/`                         | Logs, diagnostics and full resumable checkpoints; ignored                      |

Keep `NSH_DATASET_ROOT` as the external parent. Initialize/resume only from full
training checkpoints under `artifacts`, never inference-only `model.pt` exports.
Do not modify adjacent Virgo Design, replace previous models or publish the repo.

No Python model is selected yet. See [SEMANTICS.md](SEMANTICS.md).
