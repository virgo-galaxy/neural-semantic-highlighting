# C training

Use the [shared standalone workflow](../shared/README.md), same architecture and
command naming. Data stays under `~/Datasets/neural-semantic-highlighting/c`;
full runs/checkpoints stay under ignored `artifacts/c`. Preserve all existing
language data, experiments and selected models.

The existing Apple Clang and matching macOS SDK were verified with authored C11,
C17 and C23 programs. No new compiler or SDK is installed. Offline labeling builds
a pinned grammar into ignored project cache; it never compiles collected projects,
follows includes, runs a preprocessor or executes captured source. Inference needs
neither a compiler nor that parser.

```sh
make dataset-c-tools
make test-labeling-c
make test-training-data-shared
make dataset-c
make train-c-smoke C_DEVICE=mps C_RUN=artifacts/c/smoke-new
caffeinate -i make train-c C_DEVICE=mps C_EPOCHS=3 \
  C_RUN=artifacts/c/new-run \
  C_INIT_FROM=artifacts/csharp/context512-mixed-20261109-01/candidates/epoch-0003.pt
caffeinate -i make continue-c C_DEVICE=mps C_EPOCHS=3 \
  C_CHECKPOINT=artifacts/c/new-run/last.pt
```

Freeze the first prepared family assignments in `dataset/split-groups.json` before
training. Start with smoke and three measured epochs, inspect natural validation,
independent Golden and real code, then choose bounded continuations. `status.json`,
`run.json`, `epochs/*.json`, `best.pt` and `last.pt` record progress and retain full
optimizer/RNG/data identity. `C_LEARNING_RATE` controls an explicit fresh run.

Only resume the original run's `last.pt`. Changed data starts a new immutable
snapshot and explicit weights-only initialization from a compatible full training
checkpoint. Never train from `packs/*/model/model.pt` or browser ONNX exports.

```sh
make evaluate-c C_CHECKPOINT=artifacts/c/new-run/best.pt
make challenge-c C_CHECKPOINT=artifacts/c/new-run/best.pt
make evaluate-c C_CHECKPOINT=artifacts/c/new-run/frozen.pt C_EVAL_SPLIT=test
make export-c-model C_CHECKPOINT=artifacts/c/new-run/frozen.pt C_TEST_REPORT=path/to/test.json
```

Review real source before freezing a candidate; inspect independent test only then.
Document natural/focused scores and actual limits. Browser export follows the
existing [float32 ONNX workflow](../browser/README.md) and does not retrain a model.
