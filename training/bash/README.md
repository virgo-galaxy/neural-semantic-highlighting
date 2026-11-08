# Shell training

Reuse [shared training infrastructure](../shared/README.md), preserving one pack's
schema, data, frozen families, full checkpoints and inference artifact paths.
Start with smoke and a few measured epochs before selecting a bounded continuation.
Use `caffeinate -i` for training. No additional shell environment is required.

```sh
make dataset-bash
make test-labeling-bash
make train-bash-smoke BASH_DEVICE=mps
caffeinate -i make train-bash BASH_DEVICE=mps BASH_EPOCHS=3 \
  BASH_RUN=artifacts/bash/new-run \
  BASH_INIT_FROM=artifacts/go/context512-20260913-074648-569634/best.pt
caffeinate -i make continue-bash BASH_DEVICE=mps BASH_EPOCHS=3 \
  BASH_CHECKPOINT=artifacts/bash/new-run/last.pt
```

Resume `last.pt` in its original directory. A new dataset needs a fresh run with
explicit transfer from a compatible full checkpoint. Never initialize or resume
from selected `packs/*/model/model.pt` inference exports. Keep all prior data,
experiments and formal models. The repository remains private.

Selection averages per-profile natural fixed-validation role macro F1. Inspect
real source and independent Golden before freezing a candidate. Final independent
test uses the real predicted-adaptive cursor once, then export requires matching
report hashes and reviewed documentation. Preserve natural/focus breakdowns and
explicit small-coverage limits for POSIX/Bash/Zsh/Csh.

The preserved Here Document follow-up uses full checkpoints in
`artifacts/bash/context512-heredoc-20261108-01` and
`artifacts/bash/context512-heredoc-fragments-20261108-01`. The selected candidate
is frozen epoch 20 of the latter. The original test is already known; its next
evaluation is a comparison, not unseen evidence. New Here Document families had
a separate first-holdout report after candidate freezing. Keep the archived
previous inference bundle and all full checkpoints.
