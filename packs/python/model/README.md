# Python neural model

The selected inference artifact uses the existing four-layer, 128-wide byte
Transformer with a 512-byte context. Runtime consumes original source and neural
weights only; it does not import CPython AST/tokenization teachers, resolve imports
or execute code. `.py`, `.pyw` and `.pyi` share one Python entry.

The selected quality revision preserves full-checkpoint initialization and uses
additional frozen source families plus validation-selected decoder/window settings.
The original four-module regression reaches **91.48%**; the additional 19-file
cohort reaches **90.87%**. Current checkpoint and selection hashes live in
`model.json`; detailed scope is in [BENCHMARKS.md](BENCHMARKS.md). Original training
history is preserved in [the preceding bundle](../model-20261119-v1/README.md).

The inference export preserves float32 weights and removes optimizer/RNG/resume
state. Use original full checkpoints in `artifacts/python` to resume experiments.
`model.json` binds parameter count, ordered labels, weights and test report hashes.

This bounded model covers common Python display code. Source-local name
roles and long docstrings remain weaker than punctuation and keywords; inspect
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md) before
depending on exact semantic roles. f/t-strings are complete strings rather than
composed interpolation expressions. Browser/Playground inference uses the selected
ONNX model in the existing Worker. Frontend applications use `{ language: "python" }`
without a Python provider; see [consumer integration](../../../README.md#highlight-code)
and [browser verification](../../../docs/browser-runtime.md).

The Python CLI below is an optional native development/reference tool:

```sh
.venv/bin/python -m packs.python.runtime.local --file example.py
```

Use the CLI's `--checkpoint path/to/candidate.pt` option to inspect compatible
development weights without replacing this bundle or the Playground's browser
model. Repository, datasets and historical experiments remain private.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
