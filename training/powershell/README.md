# PowerShell training

Use [shared training infrastructure](../shared/README.md), preserving the PowerShell
schema, data paths, frozen families, full checkpoints and selected artifact path.

```sh
make dataset-powershell
make test-labeling-powershell
make train-powershell-smoke PowerShell_DEVICE=mps
caffeinate -i make train-powershell PowerShell_DEVICE=mps PowerShell_EPOCHS=3 \
  PowerShell_RUN=artifacts/powershell/new-run \
  PowerShell_INIT_FROM=artifacts/go/context512-20260913-074648-569634/best.pt
caffeinate -i make continue-powershell PowerShell_DEVICE=mps PowerShell_EPOCHS=3 \
  PowerShell_CHECKPOINT=artifacts/powershell/new-run/last.pt
```

No Windows/PowerShell environment is required. Resume `last.pt` in its original directory;
changed data starts a fresh explicit weights-only transfer. Never initialize or
resume from `packs/*/model/model.pt`. Select through mean per-profile natural
validation and actual code, freeze before the first independent test, then export
with matching hashes and reviewed limitations. Keep natural/focus/profile counts.
