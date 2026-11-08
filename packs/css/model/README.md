# CSS model

No inference artifact has been selected. Do not copy smoke weights here or claim
CSS/SCSS model accuracy from offline Gold fixtures.

The selected model will contain `model.pt`, `model.json`, held-out reports,
benchmarks and known issues. It must support both `css` and `scss` with explicit
per-kind evidence and retain its training/source/data provenance.

Resumable checkpoints belong under `artifacts/css/<run>/`. The selected
`model.pt` must omit optimizer/RNG/resume state and must not be used for continuation.
