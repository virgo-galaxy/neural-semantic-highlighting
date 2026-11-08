# BAT/CMD training

Use [shared training infrastructure](../shared/README.md), preserving the BAT/CMD
schema, data paths, frozen families, full checkpoints and selected artifact path.

```sh
make dataset-bat
make test-labeling-bat
make train-bat-smoke BAT_DEVICE=mps
caffeinate -i make train-bat BAT_DEVICE=mps BAT_EPOCHS=3 \
  BAT_RUN=artifacts/bat/new-run \
  BAT_INIT_FROM=artifacts/go/context512-20260913-074648-569634/best.pt
caffeinate -i make continue-bat BAT_DEVICE=mps BAT_EPOCHS=3 \
  BAT_CHECKPOINT=artifacts/bat/new-run/last.pt
```

No Windows environment is required. Resume `last.pt` in its original directory;
changed data starts a fresh explicit weights-only transfer. Never initialize or
resume from `packs/*/model/model.pt`. Select through mean per-profile natural
validation and actual code, freeze before the first independent test, then export
with matching hashes and reviewed limitations. Keep natural/focus/profile counts.
