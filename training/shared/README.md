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
