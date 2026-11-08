# Perl training

Reuse [shared training infrastructure](../shared/README.md), preserving one pack's
schema, data, frozen families, full checkpoints and inference artifact paths.
Start with smoke and a few measured epochs before selecting a bounded continuation.
Use `caffeinate -i` for training. The existing host PPI parser is sufficient; input source is never executed.

```sh
make dataset-perl
make test-labeling-perl
make train-perl-smoke PERL_DEVICE=mps
caffeinate -i make train-perl PERL_DEVICE=mps PERL_EPOCHS=3 \
  PERL_RUN=artifacts/perl/new-run \
  PERL_INIT_FROM=artifacts/go/context512-20260913-074648-569634/best.pt
caffeinate -i make continue-perl PERL_DEVICE=mps PERL_EPOCHS=3 \
  PERL_CHECKPOINT=artifacts/perl/new-run/last.pt
```

Resume `last.pt` in its original directory. A new dataset needs a fresh run with
explicit transfer from a compatible full checkpoint. Never initialize or resume
from selected `packs/*/model/model.pt` inference exports. Keep all prior data,
experiments and formal models. The repository remains private.

Selection averages per-profile natural fixed-validation role macro F1. Inspect
real source and independent Golden before freezing a candidate. Final independent
test uses the real predicted-adaptive cursor once, then export requires matching
report hashes and reviewed documentation. Preserve natural/focus breakdowns and
explicit small-coverage limits for Perl 5.
