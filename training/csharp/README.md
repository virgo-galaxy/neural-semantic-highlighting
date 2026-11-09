# C# training

Use the [shared standalone workflow](../shared/README.md), same architecture and
command naming. Data stays under `~/Datasets/neural-semantic-highlighting/csharp`;
full runs/checkpoints stay under ignored `artifacts/csharp`. Preserve all existing
language data, experiments and selected models.

No .NET SDK, Mono, CLR, Roslyn or global package is installed. Offline labeling
builds a fixed source parser using the native compiler already on the host. That
parser lives only in ignored project cache. Neither training data nor C# project
builds execute; frontend inference never imports the offline parser.

```sh
make dataset-csharp-tools
make test-labeling-csharp
make test-training-data-shared
make dataset-csharp
make train-csharp-smoke CSHARP_DEVICE=mps CSHARP_RUN=artifacts/csharp/smoke-new
caffeinate -i make train-csharp CSHARP_DEVICE=mps CSHARP_EPOCHS=3 \
  CSHARP_RUN=artifacts/csharp/new-run \
  CSHARP_INIT_FROM=artifacts/java/context512-mixed-20261109-01/candidates/epoch-0001.pt
caffeinate -i make continue-csharp CSHARP_DEVICE=mps CSHARP_EPOCHS=3 \
  CSHARP_CHECKPOINT=artifacts/csharp/new-run/last.pt
```

Freeze the first prepared family assignments in `dataset/split-groups.json` before
training. Start with smoke and three measured epochs, inspect natural validation,
independent Golden and real code, then choose bounded continuations. `status.json`,
`run.json`, `epochs/*.json`, `best.pt` and `last.pt` record progress and retain full
optimizer/RNG/data identity. `CSHARP_LEARNING_RATE` controls an explicit fresh run.

Only resume the original run's `last.pt`. Changed data starts a new immutable
snapshot and explicit weights-only initialization from a compatible full training
checkpoint. Never train from `packs/*/model/model.pt` or browser ONNX exports.

```sh
make evaluate-csharp CSHARP_CHECKPOINT=artifacts/csharp/new-run/best.pt
make challenge-csharp CSHARP_CHECKPOINT=artifacts/csharp/new-run/best.pt
make evaluate-csharp CSHARP_CHECKPOINT=artifacts/csharp/new-run/frozen.pt CSHARP_EVAL_SPLIT=test
make export-csharp-model CSHARP_CHECKPOINT=artifacts/csharp/new-run/frozen.pt CSHARP_TEST_REPORT=path/to/test.json
```

Review real source before freezing a candidate; inspect independent test only then.
Document natural/focused scores and actual limits. Browser export follows the
existing [float32 ONNX workflow](../browser/README.md) and does not retrain a model.
