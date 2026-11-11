# Shell neural model

One 893,582-parameter, four-layer byte Transformer covers POSIX sh, Bash, Zsh and
Csh/Tcsh through one Shell entry. Git Bash shares Bash syntax. Inference reads
original UTF-8 source and returns UTF-16 spans, without shell execution, a lexer,
command lookup or source-regex repairs.

The selected full checkpoint is frozen epoch 20 of the 24-epoch short Here
Document follow-up:
`artifacts/bash/context512-heredoc-fragments-20261108-01/candidates/epoch-0020.pt`.
It transfers from full training checkpoints under `artifacts/bash`, preserving the
architecture and schema. No inference bundle was used to resume training.

The first evaluation of 216 new Here Document holdout tasks measured 96.76%
exact-span F1, compared with 58.84% for the preserved previous model. The already
known natural corpus scores 84.78% overall and 93.20% for Bash. These are distinct
evidence sets; the old corpus is not newly unseen. Short-snippet terminator and
name-role errors remain in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

```sh
.venv/bin/python -m packs.bash.runtime.local --file example.sh
```

This is a float32 inference export, without optimizer or resumable state. Full
checkpoints stay under `artifacts/bash`; immutable source, Gold and prepared
snapshots stay external under `~/Datasets/neural-semantic-highlighting/bash`.
The previous formal bundle is preserved at `../model-20261108-e16`, with its
original semantic contract. The repository remains private. Playground runs the
selected ONNX model in the browser Worker, including explicit function/Here
Document examples. Frontend applications use `{ language: "bash" }` or the existing
shell aliases without a Python provider; see [consumer integration](../../../README.md#highlight-code).
The native CLI's `--checkpoint path/to/candidate.pt` selects compatible development
weights, without changing the Playground's browser model.
