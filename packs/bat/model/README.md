# BAT / CMD neural model

One 893,582-parameter byte Transformer covers common cmd.exe batch source through
one BAT / CMD entry. `.bat` and `.cmd` share the same model and document kind.
It returns original UTF-16 spans through the existing local process, renderer,
themes and Playground bridge. No Windows environment is installed or invoked;
inference imports no offline lexer and never executes batch code or subprocesses.

[BENCHMARKS.md](BENCHMARKS.md) records the selected full checkpoint, bounded
training, independent test and actual source evidence. Variable expansion, label
calls and command roles are approximate source display, not execution analysis.
Measured limitations remain in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

```sh
.venv/bin/python -m packs.bat.runtime.local --file example.cmd
```

Immutable source, Gold and prepared revisions stay external under
`~/Datasets/neural-semantic-highlighting/bat`; full resumable checkpoints stay
under `artifacts/bat`. Training transfers/resumes full checkpoints only; selected
float32 `model.pt` is inference-only. Preserve all prior models, data and runs.
Repository stays private. `NSH_BAT_CHECKPOINT` selects a compatible development
checkpoint through the same local Playground bridge.
