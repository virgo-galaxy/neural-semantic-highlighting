# Neural Semantic Highlighting

A runtime-agnostic neural semantic highlighting engine.

Current TypeScript neural runtime:

- Context: 2048 UTF-8 bytes
- Training windows: adaptive semantic cursor; unsafe cuts move to Gold span boundaries
- Inference windows: adaptive predicted cursor; unsafe cuts move to the predicted span boundary
- No fixed overlap percentage or overlap fusion in the default runtime
- RegExp: focused curriculum with halo and operator-slash negatives
- Artifacts: `artifacts/typescript/context2048`
- Training data: external, defaulting to `~/Datasets/neural-semantic-highlighting`
- Train: `make train-typescript`
