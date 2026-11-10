# Svelte training

Uses `training/shared` and the existing 512-byte, width-128 four-layer model.
Data stays in `~/Datasets/neural-semantic-highlighting/svelte`; full resumable
checkpoints/logs stay in ignored `artifacts/svelte`.

```sh
make dataset-svelte
make test-labeling-svelte
caffeinate -i make train-svelte-smoke SVELTE_DEVICE=mps SVELTE_RUN=artifacts/svelte/smoke SVELTE_INIT_FROM=artifacts/vue/context512-compact-20261108-01/best.pt
caffeinate -i make train-svelte SVELTE_DEVICE=mps SVELTE_EPOCHS=3 SVELTE_RUN=artifacts/svelte/context512 SVELTE_INIT_FROM=artifacts/vue/context512-compact-20261108-01/best.pt
make evaluate-svelte SVELTE_DEVICE=mps SVELTE_CHECKPOINT=artifacts/svelte/context512/best.pt
make challenge-svelte SVELTE_DEVICE=mps SVELTE_CHECKPOINT=artifacts/svelte/context512/best.pt
caffeinate -i make continue-svelte SVELTE_DEVICE=mps SVELTE_EPOCHS=6 SVELTE_CHECKPOINT=artifacts/svelte/context512/last.pt
```

Use a compatible **full training checkpoint** for transfer/resume. Never use
`packs/*/model/model.pt` as a training checkpoint. Archive reviewed candidates
before continuation. Review natural validation, Golden and independently authored
visible components before freezing the candidate and opening final test. Keep
base-region and composed semantic scores distinct; no score-driven unbounded runs.
