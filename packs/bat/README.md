# BAT / CMD pack

One independent neural entry covers common Windows batch source in `.bat` and
`.cmd`. It reuses the same small byte Transformer, source/Gold/Golden workflow,
UTF-16 spans, browser/native runtimes, renderer and themes as previous packs.

No Windows environment is installed and batch source is never executed.
[SEMANTICS.md](SEMANTICS.md) defines bounded labels, variables and string policy.
Immutable external data stays under `~/Datasets/neural-semantic-highlighting/bat`;
resumable checkpoints stay under `artifacts/bat`; selected `model/model.pt` is
inference-only. Preserve all previous data/models/runs. Repository stays private.
