# Assembly neural model

One small byte Transformer provides one Assembly entry for common NASM/Intel,
GNU/AT&T, MASM and AArch64 source. Assembly `.asm`, `.s`, `.S`, `.nasm`, `.masm`
and `.inc` files share the same document kind and inference model. It reuses the
existing original UTF-16 span protocol, HTML renderer, themes and browser/native
runtimes; no assembler, emulator, x86 runtime or Windows environment is installed.

The frozen complete checkpoint, exact parameter count, short training history,
first independent adaptive test and per-profile evidence are recorded in
[BENCHMARKS.md](BENCHMARKS.md). These are bounded source-display results, not ISA
validation or execution compatibility. Remaining failures are explicit in
[KNOWN_ISSUES.md](KNOWN_ISSUES.md).

```sh
.venv/bin/python -m packs.assembly.runtime.local --file example.asm
```

Inference consumes only original text and model weights: no offline lexer,
architecture detector, macro expansion, include following or source-regex repair.
The float32 `model.pt` export is inference-only. Training initializes/resumes from
full checkpoints under `artifacts/assembly`, never an inference export. Immutable
source, Gold and prepared revisions remain external under
`~/Datasets/neural-semantic-highlighting/assembly` with complete source licenses.
Preserve all prior data/models/experiments and keep the repository private.
Playground and frontend consumers use the selected ONNX model in the browser
Worker with `{ language: "assembly" }`, without a Python provider; see
[consumer integration](../../../README.md#highlight-code). The native CLI's
`--checkpoint path/to/candidate.pt` selects compatible development weights,
without changing the Playground's browser model.
