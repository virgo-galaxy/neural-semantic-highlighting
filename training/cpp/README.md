# C++ training

Use the [shared standalone workflow](../shared/README.md), same architecture and
command naming. Data stays under `~/Datasets/neural-semantic-highlighting/cpp`;
full runs/checkpoints stay under ignored `artifacts/cpp`. Preserve all existing
language data, experiments and selected models.

The existing Apple Clang and matching macOS SDK were verified with authored C++17,
C++20 and C++23 programs. No new compiler or SDK is installed. Offline labeling builds
a pinned grammar into ignored project cache; it never compiles collected projects,
follows includes, runs a preprocessor or executes captured source. Inference needs
neither a compiler nor that parser.

```sh
make dataset-cpp-tools
make test-labeling-cpp
make test-training-data-shared
make dataset-cpp
make train-cpp-smoke CPP_DEVICE=mps CPP_RUN=artifacts/cpp/smoke-new
caffeinate -i make train-cpp CPP_DEVICE=mps CPP_EPOCHS=3 \
  CPP_RUN=artifacts/cpp/new-run \
  CPP_INIT_FROM=artifacts/c/context512-mixed-20261109-01/candidates/epoch-0002.pt
caffeinate -i make continue-cpp CPP_DEVICE=mps CPP_EPOCHS=3 \
  CPP_CHECKPOINT=artifacts/cpp/new-run/last.pt
```

Freeze the first prepared family assignments in `dataset/split-groups.json` before
training. Start with smoke and three measured epochs, inspect natural validation,
independent Golden and real code, then choose bounded continuations. `status.json`,
`run.json`, `epochs/*.json`, `best.pt` and `last.pt` record progress and retain full
optimizer/RNG/data identity. `CPP_LEARNING_RATE` controls an explicit fresh run.

Only resume the original run's `last.pt`. Changed data starts a new immutable
snapshot and explicit weights-only initialization from a compatible full training
checkpoint. Never train from `packs/*/model/model.pt` or browser ONNX exports.

```sh
make evaluate-cpp CPP_CHECKPOINT=artifacts/cpp/new-run/best.pt
make challenge-cpp CPP_CHECKPOINT=artifacts/cpp/new-run/best.pt
make evaluate-cpp CPP_CHECKPOINT=artifacts/cpp/new-run/frozen.pt CPP_EVAL_SPLIT=test
make export-cpp-model CPP_CHECKPOINT=artifacts/cpp/new-run/frozen.pt CPP_TEST_REPORT=path/to/test.json
```

Review real source before freezing a candidate; inspect independent test only then.
Document natural/focused scores and actual limits. Browser export follows the
existing [float32 ONNX workflow](../browser/README.md) and does not retrain a model.
