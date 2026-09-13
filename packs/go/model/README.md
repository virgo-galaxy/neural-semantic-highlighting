# Go model

This directory contains the selected Go inference artifact and its identity/evaluation records.
It is the canonical runtime model location for the Go pack; local experiment checkpoints stay under
`artifacts/go/` and are not runtime dependencies.

## Runtime contract

The selected Go runtime is neural-only:

```text
Go source
  ↓
selected model (`packs/go/model/model.pt`)
  ↓
predicted adaptive cursor + greedy span decoding
  ↓
HighlightResult (UTF-16 offsets)
```

The runtime does **not** invoke the Go scanner, parser, AST, type checker, compiler, language
server, or any other Go toolchain component. Go tooling may be used offline to construct Gold
training/evaluation labels; it is not part of inference.

The model consumes UTF-8 bytes with a 512-byte context and predicts BIO boundaries, token types,
and modifiers. The selected artifact is produced from a reviewed training checkpoint with:

```bash
make export-go-model \
  GO_CHECKPOINT=artifacts/go/<run>/best.pt \
  GO_TEST_REPORT=artifacts/go/<run>/test-adaptive-<stamp>.json
```

The exporter removes optimizer/RNG/resume state and writes:

```text
packs/go/model/model.pt
packs/go/model/model.json
packs/go/model/reports/test-metrics.json
```

The exported `model.pt` is an inference artifact and must not be used with `train.py --resume`.
Resume training from the original checkpoint under `artifacts/go/`.

## Selected candidate

The currently promoted candidate is epoch 29 from the canonical 512-byte Go run. Independent
pure-neural adaptive evaluation measured:

- natural test exact-span F1: `0.9903`;
- natural test exact-span macro F1: `0.9676`;
- focused test exact-span F1: `0.9875`;
- focused test exact-span macro F1: `0.9571`.

The Playground was also checked with ordinary Go, structs/fields/methods, generics, selector chains,
and long raw strings before promotion.

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for the remaining measured limits. The raw held-out report is
stored in `reports/test-metrics.json` when the model is exported.
