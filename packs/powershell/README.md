# PowerShell pack

One entry covers common PowerShell script, module and module-data source.
It reuses the independent small Transformer, UTF-16 spans, local process,
renderer/themes and established source/Gold/Golden/training workflow.

No Windows, pwsh or .NET environment is installed or invoked. Offline display
Gold uses pinned lexer machinery and bounded source-local roles; inference is
pure neural. Read [SEMANTICS.md](SEMANTICS.md) for opaque strings and role limits.
External immutable data stays under `~/Datasets/neural-semantic-highlighting/powershell`,
full checkpoints under `artifacts/powershell`; selected `model/model.pt` is
inference-only. Preserve all previous data/models/experiments; remain private.
