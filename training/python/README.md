# Python training

Commands preserve the existing pack workflow and reuse [shared primitives](../shared/README.md).
Keep datasets under `~/Datasets/neural-semantic-highlighting/python` and full
checkpoints under ignored `artifacts/python`. Existing snapshots and experiments
are immutable history, not files to overwrite when making a revision.

```sh
make test-labeling-python
make test-training-data-shared
make dataset-python
make train-python-smoke PYTHON_DEVICE=mps
caffeinate -i make train-python PYTHON_DEVICE=mps PYTHON_EPOCHS=3 \
  PYTHON_RUN=artifacts/python/new-run \
  PYTHON_INIT_FROM=artifacts/go/context512-20260913-074648-569634/best.pt
caffeinate -i make continue-python PYTHON_DEVICE=mps PYTHON_EPOCHS=3 \
  PYTHON_CHECKPOINT=artifacts/python/new-run/last.pt
```

Freeze source-family assignments before the first training pass. The separate
Gold Python is an offline-only tool; `PYTHON_GOLD` can point at an existing modern
CPython. Data commands do not install an interpreter. Parsing never executes
source or imports its dependencies. Keep the existing PyTorch environment intact.

Start with smoke and a few real epochs, then use measured epoch timings to choose
a bounded continuation. `status.json`, `epochs/*.json`, `run.json`, `best.pt` and
`last.pt` record progress, provenance and resumable optimizer/RNG state. Resume
only `last.pt` in the existing run; a dataset change needs a new run with explicit
weights-only initialization from a compatible full checkpoint. Never train from
`packs/*/model/model.pt`.

Inspect real validation failures and independent Golden, freeze a reviewed
candidate, then evaluate independent test once. Natural and focused grammar
scores stay separate. Export requires a hash-matching test report and reviewed
README/BENCHMARKS/KNOWN_ISSUES, refuses to replace an existing model, and strips
training state. The current selected model's test has already been inspected;
future measurements on those files are not new unseen-test evidence.

```sh
make evaluate-python PYTHON_CHECKPOINT=artifacts/python/new-run/best.pt
make challenge-python PYTHON_CHECKPOINT=artifacts/python/new-run/best.pt
make evaluate-python PYTHON_CHECKPOINT=artifacts/python/new-run/frozen.pt PYTHON_EVAL_SPLIT=test
make export-python-model PYTHON_CHECKPOINT=artifacts/python/new-run/frozen.pt PYTHON_TEST_REPORT=path/to/test.json
```

Existing formal models are preserved. A future promotion must first preserve the
current Python bundle as a versioned historical artifact instead of overwriting it.
