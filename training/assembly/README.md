# Assembly training

Follow the [shared standalone workflow](../shared/README.md) with the same source,
Gold/Golden, frozen families, full checkpoints, first-test review and export steps.

```sh
make dataset-assembly
make test-labeling-assembly
make train-assembly-smoke ASSEMBLY_DEVICE=mps
caffeinate -i make train-assembly ASSEMBLY_DEVICE=mps ASSEMBLY_EPOCHS=3 \
  ASSEMBLY_RUN=artifacts/assembly/new-run \
  ASSEMBLY_INIT_FROM=artifacts/go/context512-20260913-074648-569634/best.pt
caffeinate -i make continue-assembly ASSEMBLY_DEVICE=mps ASSEMBLY_EPOCHS=3 \
  ASSEMBLY_CHECKPOINT=artifacts/assembly/new-run/last.pt
```

No native assembler/Windows/x86 runtime is required. Resume `last.pt` in its own
run; changed data/configuration starts an explicit weights-only transfer from a
compatible complete checkpoint. Never use `packs/*/model/model.pt` for training.
Measure short epochs before extending a budget; `caffeinate -i` prevents idle
system sleep while the command runs. Check actual code per profile, freeze before
the first independent test, then export with matching hashes and honest limits.
