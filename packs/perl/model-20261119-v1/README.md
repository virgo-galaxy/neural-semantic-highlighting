# Perl neural model

The selected 894,227-parameter byte Transformer highlights Perl 5 through the
browser Worker or optional native Python runtime. It returns original UTF-16
spans without invoking
Perl, PPI, a compiler, source regex repairs or command execution at inference.

Frozen epoch 9 of
`artifacts/perl/context512-fragments-v2-20261108-01/candidates/epoch-0009.pt`
was selected after short staged training, natural validation, Golden and actual
code inspection. Full checkpoints remain under `artifacts/perl`; this float32
export contains inference weights, not optimizer/RNG or resumable training state.

The first natural test measured 83.60% exact-span F1 on four host core modules;
focused test F1 is 88.21%. These small samples are bounded evidence. Ordinary
script, regex, object-call and standalone Here Document examples are usable;
consecutive mixed Here Documents and rare name/modifier boundaries remain weaker.
See [BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

```sh
.venv/bin/python -m packs.perl.runtime.local --file example.pl
```

Data/Gold/immutable snapshots stay external under
`~/Datasets/neural-semantic-highlighting/perl`. Offline Gold uses already available
host PPI 1.270; source is parsed as text, never compiled or executed. No additional
language environment was installed. Existing datasets, experiments and formal
models are preserved. The repository remains private. Playground and frontend
consumers use the selected ONNX model in the browser Worker with
`{ language: "perl" }`, without a Python provider; see [consumer integration](../../../README.md#highlight-code).
The native CLI's `--checkpoint path/to/candidate.pt` selects compatible development
weights, without changing the Playground's browser model.
