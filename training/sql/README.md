# SQL training

Use [shared training infrastructure](../shared/README.md), preserving the SQL
schema, data paths, frozen families, full checkpoints and selected artifact path.

```sh
make dataset-sql
make test-labeling-sql
make train-sql-smoke SQL_DEVICE=mps
caffeinate -i make train-sql SQL_DEVICE=mps SQL_EPOCHS=3 \
  SQL_RUN=artifacts/sql/new-run \
  SQL_INIT_FROM=artifacts/go/context512-20260913-074648-569634/best.pt
caffeinate -i make continue-sql SQL_DEVICE=mps SQL_EPOCHS=3 \
  SQL_CHECKPOINT=artifacts/sql/new-run/last.pt
```

No database environment is required. Resume `last.pt` in its original directory;
changed data starts a fresh explicit weights-only transfer. Never initialize or
resume from `packs/*/model/model.pt`. Select through mean per-profile natural
validation and actual code, freeze before the first independent test, then export
with matching hashes and reviewed limitations. Keep natural/focus/profile counts.
