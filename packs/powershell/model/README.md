# PowerShell neural model

One 893,969-parameter byte Transformer covers common PowerShell scripts, modules
and module-data source through one entry. The same local process bridge returns
original UTF-16 spans for existing renderers/themes. It neither requires nor
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
and historical experiments. Repository stays private. `NSH_POWERSHELL_CHECKPOINT`
selects a compatible development checkpoint through Playground's local bridge.
