# PowerShell neural model

One 893,969-parameter byte Transformer covers common PowerShell scripts, modules
and module-data source through one entry. Browser and optional native runtimes
return original UTF-16 spans for existing renderers/themes. It neither requires nor
installs Windows, pwsh or .NET; inference imports no offline lexer and never
executes code, modules, commands or embedded strings.

The selected frozen full checkpoint, short training budget, independent test and
actual code evidence are recorded in [BENCHMARKS.md](BENCHMARKS.md). Common
Windows PowerShell/modern PowerShell source is the scope, not full version or
module execution compatibility. Both quote forms of Here-String use opaque
string spans; interpolation is not recursively highlighted. Measured limitations
remain in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

```sh
.venv/bin/python -m packs.powershell.runtime.local --file example.ps1
```

External immutable source, Gold and prepared snapshots stay under
`~/Datasets/neural-semantic-highlighting/powershell`; resumable training checkpoints
stay under `artifacts/powershell`. Only full checkpoints initialize/resume training.
The float32 `model.pt` export is inference-only. Preserve all prior models, data
and historical experiments. Repository stays private. Playground and frontend
consumers use the selected ONNX model in the browser Worker with
`{ language: "powershell" }`, without a Python provider; see
[consumer integration](../../../README.md#highlight-code). The native CLI's
`--checkpoint path/to/candidate.pt` selects compatible development weights,
without changing the Playground's browser model.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
