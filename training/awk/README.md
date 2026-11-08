# AWK training

Use the [shared workflow](../shared/README.md) and preserve pack-owned paths,
schema, frozen families, historical data and full checkpoints.

```sh
make dataset-awk
make test-labeling-awk
make train-awk-smoke AWK_DEVICE=mps
caffeinate -i make train-awk AWK_DEVICE=mps AWK_EPOCHS=3 \
  AWK_RUN=artifacts/awk/new-run \
  AWK_INIT_FROM=artifacts/perl/context512-fragments-v2-20261108-01/candidates/epoch-0009.pt
caffeinate -i make continue-awk AWK_DEVICE=mps AWK_EPOCHS=3 \
  AWK_CHECKPOINT=artifacts/awk/new-run/last.pt
```

Resume `last.pt` in its original directory. A new snapshot uses explicit
weights-only transfer into a fresh run. Never initialize/resume from an inference
export under `packs/*/model`. Select through natural validation and actual code,
freeze a candidate before the first independent test, then export with matching
reports and reviewed limitations. No additional AWK environment is required.
