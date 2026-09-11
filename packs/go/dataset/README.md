# Go Dataset Pipeline

This directory contains the internal dataset tooling for the Go semantic pack.
It is not part of the public NSH runtime contract.

## Current phase

The first corpus layer is the production source of the **Go 1.27.1 standard library**.
The pipeline intentionally starts here before adding `golang.org/x/...`, public modules, and
selected large real-world projects.

The current commands are:

```bash
make dataset-go-collect
make dataset-go-label
make dataset-go-validate
```

Or run the complete first-layer pipeline:

```bash
make dataset-go
```

The commands require the Go Gold toolchain pinned by the repository:

```text
go1.27.1
```

## External dataset location

Dataset artifacts are kept outside the repository.

By default:

```text
~/Datasets/neural-semantic-highlighting/go/
```

Override the common dataset root with:

```bash
NSH_DATASET_ROOT=/path/to/datasets make dataset-go
```

The Go-specific subdirectory is appended automatically.

## Outputs

```text
go/
├── sample.json
├── labeled-sample.jsonl
└── statistics.json
```

`sample.json` is deterministic for the same Go toolchain and build context. It records source
content hashes so labeling and validation fail if the underlying standard-library source changes
between stages.

`labeled-sample.jsonl` is a compact streaming JSON Lines file. Each line contains one source file and
its package-aware Gold `HighlightResult`. JSON Lines keeps the corpus practical as later module
layers grow beyond the standard library and avoids loading the complete labeled corpus into memory.

`statistics.json` records corpus size and semantic-role distributions.

## Package-aware labeling

Real Go packages distribute declarations and uses across multiple source files. Dataset labeling
therefore type-checks the active files of a package together instead of labeling every file in
isolation.

The single-file `labeling.Label` API remains available for fixtures and focused cases, but the
corpus pipeline uses `labeling.LabelPackage`.

## Selection policy

The first standard-library pass uses files reported by:

```bash
go list -json std
```

Only production `GoFiles` in the active build context are selected. Test files and inactive
platform/build-tag variants are not part of this first layer. Files smaller than 200 bytes or larger
than 100,000 bytes are excluded to avoid trivial stubs and large table-heavy sources dominating the
baseline.

This is intentionally a baseline, not the final Go corpus. Later corpus layers will add modern-Go
focused examples, additional build contexts, official `golang.org/x/...` repositories, and selected
public modules.
