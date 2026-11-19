# Shared standalone-pack workflow

New standalone packs reuse the existing four-layer byte Transformer, masked
losses, fixed validation windows and predicted adaptive inference. Existing
TypeScript, Go, CSS, HTML and Vue implementations and selected weights stay intact.

Each new pack owns `manifest.json`, `schema.json`, `SEMANTICS.md`, `pack.json`,
offline teacher, sources, frozen source-family assignments, Golden and model bundle.
`training/<pack>` preserves the established command names. `using(pack_id)` scopes
offline command configuration with a context variable; runtime objects retain their
own model/schema and can coexist without changing another pack's configuration.

Optional pack-owned decoder policies declare canonical touching regions and valid
modifier/role combinations. Defaults preserve the original standalone behavior.
Gold, validation and runtime must share those rules; they never inspect source
spelling or repair a predicted type. Custom policies require a checkpoint-bound
pack-configuration hash. Changing a policy starts a new experiment/protocol, with
old reports and checkpoints preserved rather than silently reinterpreted.

Data stays under `$NSH_DATASET_ROOT/<pack>` (default
`~/Datasets/neural-semantic-highlighting/<pack>`), with immutable `corpora`, `gold`
and `prepared` snapshots. Every source retains original UTF-8 bytes and origin,
license/provenance text and hashes. Invalid teacher output is quarantined. No
collected source is imported or executed. Golden and Playground are never roots.

Exact, lexical and identifier-normalized copies crossing source families are
excluded before grouped allocation. Freeze the first prepared family map in
`packs/<pack>/dataset/split-groups.json` before training. Revisions retain that map.
Training windows can use Gold cuts; validation/test windows cannot. Natural and
original focus curriculum scores are reported separately, including every profile.

Full checkpoints live under ignored `artifacts/<pack>/<run>` and include optimizer,
RNG, dataset identity and code hashes. Resume `last.pt` in its original run; use a
compatible full checkpoint for explicit weights-only transfer into a fresh run.
Inference-only `packs/*/model/model.pt` is never a training checkpoint.

Use short smoke/initial experiments and measure epoch times before expanding a
budget. Select using natural per-profile validation macro F1, inspect real code
and independent Golden, then freeze one candidate for held-out adaptive testing.
Export requires matching test evidence and model documentation, refuses overwrite,
and strips optimizer/RNG while preserving every selected weight.

The repository remains private. External corpora and ignored training artifacts
are not committed or published; reviewed inference bundles and reports are tracked.

## Bounded quality refinement

Use a full `artifacts/<pack>/<run>/best.pt` for `--init-from`, or its `last.pt`
for an exact run resume. Never initialize training from an inference bundle.
`--sampling shuffled-windows` replays every prepared training window;
`natural-plus-curriculum` retains bounded rotating focus exposure. Record
`--selection-metric profile-f1` (or `minimum-profile-f1` for dialects) explicitly
when selecting by natural exact-span F1 instead of the historical role-macro score.

`--relative-attention` adds one learned distance slope per layer/head, initialized
at zero. Existing tensors and context remain intact. The portable native and ONNX
graphs share the same attention implementation. `--ascii-case-tied` is BAT-only:
training ties upper/lower ASCII byte embeddings and their gradients. Inference
still receives original bytes and returns original UTF-16 offsets.

Optional validation-only post-training stages:

```sh
.venv/bin/python -m training.shared.average --pack ruby \
  --checkpoints artifacts/ruby/<primary>/best.pt artifacts/ruby/<other>/best.pt \
  --output artifacts/ruby/<new-stage>/averaged.pt
.venv/bin/python -m training.shared.calibrate --pack ruby \
  --checkpoint artifacts/ruby/<new-stage>/averaged.pt \
  --output artifacts/ruby/<new-stage>/calibrated.pt --device cpu
```

Averaging checks every parent's training families against target holdouts, selects
convex weights on natural validation, and explicitly resets the optimizer/RNG.
Calibration fits transitions on natural training Gold and selects its positive
weight grid on natural validation; the unchanged decoder remains a candidate.
Neither stage uses test predictions. Preserve their reports and hashes for export.
Historical tests already inspected during development are regression evidence;
keep any newly frozen family holdout and first-read result separate.
