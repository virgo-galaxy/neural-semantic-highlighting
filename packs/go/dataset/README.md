# Go Dataset Pipeline

This directory contains internal corpus tooling, not a public NSH runtime dependency.
The repository Gold toolchain remains `go1.27.1`.

## Commands

The existing standard-library commands and paths remain valid:

```bash
make dataset-go
```

Run one official module first:

```bash
make dataset-go-official GO_CORPUS=x-sync
```

Run every explicitly configured official module:

```bash
make dataset-go-official
```

The source configuration is `packs/go/dataset/sources/official.json`. The initial allowlist contains
`golang.org/x/sync`, `x/mod`, `x/net`, `x/text`, `x/crypto`, `x/sys`, and `x/tools`.
No GitHub crawler, global package installation, or new repository module dependency is required.
The first run requires access to the configured Go module proxy and checksum services.

The CLI also accepts an explicit source configuration. Run from `packs/go`:

```bash
GOTOOLCHAIN=go1.27.1 go run ./dataset/cmd/nsh-go-dataset modules \
  --config dataset/sources/official.json --source x-sync
```

## External layout

Default dataset root:

```text
~/Datasets/neural-semantic-highlighting/go/
```

`NSH_DATASET_ROOT` overrides the common parent; `/go` is appended automatically.

```text
go/
  sample.json                    Existing standard-library manifest
  labeled-sample.jsonl            Existing standard-library Gold documents
  statistics.json                Existing standard-library statistics
  corpora/
    x-sync/
      source.lock.json
      workspace/
        go.mod
        go.sum
      sample.json
      labeled-sample.jsonl
      statistics.json
    x-mod/
      ...
  cache/
    modules/
    build/
```

Running module collection does not move, delete, or overwrite the existing standard-library corpus.
Each module has a separate namespace. File paths inside its manifest are module-relative, not local
absolute paths. Keep each JSONL file with its manifest; source identity belongs to the manifest.

## Source identity and replay

Each source config entry has an `id`, `module`, and `version` query. `latest` is allowed only as the
initial resolution policy. After the first successful preparation, `source.lock.json` records the
resolved version, module checksum, `go.mod` checksum, language directive, toolchain, build platform,
and a hash of the external workspace's resolved `go.mod` and `go.sum`.

Later runs reuse the locked version even when `latest` has advanced. The workspace hash detects
unintended dependency changes. Module checksums are verified through Go's normal download mechanism,
and cached modules are verified before labeling. Module corpus manifests use format version 2;
existing standard-library format version 1 remains readable.

Use a new corpus ID to create a new version, toolchain, or platform snapshot. Do not edit a lock to
make old outputs appear current. A module requiring a newer Go toolchain fails explicitly; the
collector does not silently upgrade the pinned Gold toolchain or fall back to an older source.

The module cache retains upstream archive contents, including supplied license files. Retain source
and version provenance when assembling or distributing any derived dataset.

## Module-aware Gold

The pipeline prepares an external consumer module and uses:

```text
go list -deps -export -json
```

This selects the active package files and produces dependency export data. A `go/importer` instance
with an explicit export lookup feeds the strict package labeler. Every selected package is checked
with all its active source files, including files excluded from sampling by size. Those context
files have their own hashes in the manifest.

A missing import, parse error, type error, changed source, or failed validation stops the corpus.
The pipeline does not turn a partially checked package into apparently valid Gold. Dependencies
supply type information; they do not become sampled training documents unless separately configured.

The single-file fixture API retains its existing behavior. The legacy standard-library pipeline is
also retained; this update does not retroactively certify previously generated documents as strict
module-corpus output. Before combining an older standard-library corpus with new labels, regenerate
its Gold and statistics with the current labeler:

```bash
make dataset-go-label
make dataset-go-validate
```

Source collection does not need repeating when the standard-library files and build context are
unchanged. This matters because the updated labeler fixes embedded type-use classification and
carriage-return boundaries.

## Selection and limits

The first module pass uses production `GoFiles` for the host OS and architecture with
`CGO_ENABLED=0`. It excludes test files, cgo-only packages, inactive build-tag variants, and files
outside the selected module. Files smaller than 200 bytes or larger than 100,000 bytes are excluded
from sampling, but not from the context of a selected package.

Assembly may be compiled for export generation. `go generate`, package test binaries, application
entry points, and framework initialization code are not executed. This is not a general-purpose
security sandbox for arbitrary untrusted modules; collection uses an explicit source allowlist.

Statistics report each corpus independently. This phase does not merge corpora, deduplicate near
copies, assign dataset splits, create 512-byte windows, or train a model. Split and duplicate-group
assignment must happen at document/module level before windowing, not after overlapping or related
windows have been mixed together.

Struct tags remain whole `string` spans. Doc comments and directives remain `comment`. Corpus
presence and passing Gold fixtures are not held-out evidence of neural model quality.

## Environment and output safety

Subprocess-only settings isolate the collector's Go workspace and module/build caches under the
external dataset root. The collector does not use `go env -w`, change `PATH`, install global tools,
edit the NSH `go.mod`, or write caches into the repository. Existing proxy and checksum preferences
are respected; production collection does not disable the checksum database.

Each corpus has an exclusive `.dataset.lock` while running. Normal exit removes it. After a hard
kill, remove a stale lock only after confirming no collection process is active. Do not remove
source locks or historical corpus data as a routine retry step.

Labeling and validation run in a temporary staging directory. Completed files are published only
after validation succeeds; failures before publication leave the previous completed outputs intact.
If a process is interrupted during publication, rerun the corpus before consuming its outputs.

## Tests

`make check` includes the Go tests. Dataset tests use temporary `file://` proxies containing neutral
synthetic modules; they need no public-module downloads. They exercise real Go module resolution,
external dependency exports, lock replay, original-byte hashes, context-file retention, malformed
identity rejection, and preservation of existing standard-library artifacts.

The metadata tests assert actual span boundaries independently of generated fixture snapshots.
No test requires installing or importing GORM, Gin, or a validator framework into NSH.

## References

- [Go Modules Reference](https://go.dev/ref/mod)
- [Go command documentation](https://pkg.go.dev/cmd/go)
- [Go importer documentation](https://pkg.go.dev/go/importer)
- [Go struct types](https://go.dev/ref/spec#Struct_types)
- [StructTag conventions](https://pkg.go.dev/reflect#StructTag)
