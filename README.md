# Neural Semantic Highlighting

A runtime-agnostic neural semantic highlighting engine.

Current TypeScript neural runtime:

- Context: 8192 UTF-8 bytes
- Sliding-window stride: 6144 bytes (2048-byte base overlap)
- Training data: external, defaulting to `~/Datasets/neural-semantic-highlighting`
- Train: `make train-typescript`
