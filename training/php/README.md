# PHP training

Use the [shared standalone workflow](../shared/README.md), same architecture and
command naming. Data stays under `~/Datasets/neural-semantic-highlighting/php`;
full runs/checkpoints stay under ignored `artifacts/php`. Preserve all existing
language data, experiments and selected models.

No PHP interpreter, Composer, web server, language SDK or global package is
installed. The host's existing native compiler builds a fixed offline parser in
ignored project cache. Collected code, includes and autoloaders are never run.
Browser consumers need neither PHP nor that parser.

```sh
make dataset-php-tools
make test-labeling-php
make test-training-data-shared
make dataset-php
make train-php-smoke PHP_DEVICE=mps PHP_RUN=artifacts/php/smoke-new
caffeinate -i make train-php PHP_DEVICE=mps PHP_EPOCHS=3 \
  PHP_RUN=artifacts/php/new-run \
  PHP_INIT_FROM=artifacts/cpp/context512-mixed-v2-20261109-01/candidates/epoch-0002.pt
caffeinate -i make continue-php PHP_DEVICE=mps PHP_EPOCHS=3 \
  PHP_CHECKPOINT=artifacts/php/new-run/last.pt
```

Freeze the first prepared family assignments in `dataset/split-groups.json` before
training. Start with smoke and three measured epochs, inspect natural validation,
independent Golden and real code, then choose bounded continuations. `status.json`,
`run.json`, `epochs/*.json`, `best.pt` and `last.pt` record progress and retain full
optimizer/RNG/data identity. `PHP_LEARNING_RATE` controls an explicit fresh run.

Only resume the original run's `last.pt`. Changed data starts a new immutable
snapshot and explicit weights-only initialization from a compatible full training
checkpoint. Never train from `packs/*/model/model.pt` or browser ONNX exports.

```sh
make evaluate-php PHP_CHECKPOINT=artifacts/php/new-run/best.pt
make challenge-php PHP_CHECKPOINT=artifacts/php/new-run/best.pt
make evaluate-php PHP_CHECKPOINT=artifacts/php/new-run/frozen.pt PHP_EVAL_SPLIT=test
make export-php-model PHP_CHECKPOINT=artifacts/php/new-run/frozen.pt PHP_TEST_REPORT=path/to/test.json
```

Review real source before freezing a candidate; inspect independent test only then.
Document natural/focused scores and actual limits. Browser export follows the
existing [float32 ONNX workflow](../browser/README.md) and does not retrain a model.
