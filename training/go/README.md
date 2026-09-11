# Go Training

This directory prepares model inputs and trains the first local Go neural baseline.
See [TRAINING.md](TRAINING.md) for smoke training, full runs, checkpoint resume,
source prediction, and evaluation. No Go model is selected or published automatically.

The sections below describe the existing data-preparation pipeline.
The Go Gold toolchain remains `go1.27.1`; Python preparation uses the existing
project environment and the Python standard library only. A lazy, persistent
Go parser helper can repair a specific legacy declaration omission. Its
`GOTOOLCHAIN=go1.27.1` setting applies only to that child process. Data preparation needs no additional Python package, global installation, saved
environment setting, or Go module dependency. Training and its new tests use
PyTorch from the existing project `.venv`, as the TypeScript trainer already does.

## Run from the repository root

```bash
make check
make dataset-go-applications
make dataset-go-targeted
make dataset-go-focused-v2
make dataset-go-prepare
```

Do not rerun `make dataset-go`, `make dataset-go-official`, or standard-library
labeling just to prepare these windows. Existing completed Gold files are read,
not overwritten. The application command adds only the explicitly selected Gin
and GORM module implementations. These are useful framework source samples, not
a claim that arbitrary real-world application patterns are already covered.
The existing collector locks versions and keeps dependencies outside the repository.

`training/go/corpora.json` explicitly selects the standard library, seven official
modules, two application-framework modules, the V2 focused curriculum, and a
train-only targeted-real curriculum mined from explicitly allowlisted modules.
Missing sources cause a clear error instead of silently creating a smaller dataset.
The corpus selector can be supplied explicitly with `prepare.py --config`.

## First focused curriculum

The generator lives in `packs/go/dataset/focused_templates.go` and creates 12
feature groups, three independently written structural forms per feature, and
16 variants per form: 36 template families and 576 source documents. Renamed
variants are not independent examples and must never be counted as such.
The three forms are reserved for training, validation, and test respectively;
all variants of one form remain together.

The initial groups are generic functions/types/constraints, Go 1.20 comparable
and array-conversion cases, Go 1.21 built-ins, integer range, function range,
generic aliases, expression-valued `new`, self-referential constraints, generic
methods, promoted-field literals, generalized function inference, and struct tags.
This is a small seed curriculum, not complete coverage of every item in
`packs/go/COVERAGE.md`. For version-specific groups, the version metadata records feature introduction.
For core constructs such as struct tags, 1.18 denotes the minimum targeted era,
not their historical introduction. Neither denotes the compiler used to create Gold.

Every generated document is formatted and strictly type-checked by the pinned
Go toolchain. No generated program, framework initialization, `go generate`, or
application entry point is executed. Fixtures and challenge cases are not copied
into this curriculum. Tags remain whole `string` spans; comments and directives
remain `comment` spans. No new token type or framework-specific role is added.

The held-out template forms are useful pipeline diagnostics. They are not a
replacement for an independent, real-source challenge set or unseen-project
model evaluation. Template variants differ in names, numeric types, and values;
the reported variant count must not be presented as architectural diversity.

## Focused Curriculum V2 and targeted real-source mining

V2 keeps the non-targeted V1 feature families but replaces the five known weak
families with multiple independent source shapes rather than one shape plus renamed
variants. The targeted families are `self-reference`, `function-range`,
`generic-method`, `generic-alias`, and `struct-tags`. Each has multiple train
structures, at least two independent validation structures, at least two independent
test structures, and train-only hard negatives. Variants still change names and
primitive types, but no longer stand in for structural diversity.

The targeted miner is intentionally not a broad GitHub crawler. It downloads only
modules listed in `packs/go/dataset/sources/targeted.json`, runs the existing strict
Gold pipeline, parses each source file, and keeps only files that contain reliable
source-level target structures. The mined records are train-only focused examples;
validation and test remain structurally independent generated families. This avoids
turning files already used for natural evaluation into duplicated focused training
examples.

Run the V2 inputs with:

```bash
make dataset-go-targeted
make dataset-go-focused-v2
make dataset-go-prepare
```

The first allowlisted real-world seed is a Go 1.27 generic-method library. The
allowlist is deliberately small and auditable; expand it only when a module adds
new structural evidence for one of the target features.

After preparation, initialize a new V2 run from a protected V1 `best.pt` without
reusing its optimizer, RNG, early-stopping state, or old dataset identity:

```bash
make train-go-v2 \
  GO_INIT_CHECKPOINT=artifacts/go/context512-RUN/best.pt \
  GO_EPOCHS=1
```

`--init-from` is weights-only transfer to a new prepared snapshot. It is distinct
from `--resume`, which is valid only for `last.pt` on the exact saved snapshot.
Start with one short V2 epoch, inspect the targeted role scoreboard, then extend
only if the weak roles improve without a material natural-code regression.

## Grouping before windows

The builder validates each JSONL record against its manifest, content hash,
UTF-16 boundaries, token vocabulary, and span ordering. It retains source/version
provenance and builds a disk-backed index rather than loading all JSONL data at once.

Exact duplicate sources are stored once. Conflicting Gold for identical source
bytes stops preparation; one source is not arbitrarily chosen as correct.
Whole-document lexical fingerprints ignore comments and layout. Shape
fingerprints additionally normalize non-builtin identifiers and literal values.
The original source bytes and retained labels remain unchanged.

Module versions and platform variants share one module group. Standard-library
packages share their top-level subsystem; `internal` packages use the next path
component as well. Focused records share their explicitly assigned template family.

Copy detection links **documents**, not their entire parent modules. When a
natural exact/lexical/shape-copy family appears in multiple source groups, all
members of that copy family are excluded from model inputs. Their document hashes
and provenance are recorded in `cross-group-copies.jsonl`; no original Gold file
is changed or deleted. This is distinct from incomplete-Gold quarantine. It avoids
both cross-split duplicates and a chain of shared files merging most of the corpus
into a single indivisible group. Within-source near copies remain in the same split.
A copy link between two different preassigned focused splits is still a hard error.

Natural source groups are assigned with deterministic, size-aware balancing toward
80/10/10. The assignment weight is the number of character-safe fixed windows,
computed before assignment and without Gold-adaptive cuts. A largest-first pass
and whole-group reassignments improve the balance without splitting modules,
subsystems, documents, or focused families. `split-groups.json` records the choices.

Actual natural-window ratios are checked after encoding. Train must contain
70-90 percent and each holdout 5-20 percent of natural windows. These are guardrails
around the target, not exact quotas. Focused windows cannot satisfy these checks.
An infeasible split fails instead of publishing misleading evaluation data. The
manifest reports natural/focused token distributions separately; presence in the
focused stream must not be presented as natural-source coverage.

Partial-file clones and arbitrary semantic similarity are not detected by this
baseline. Whole-module/subsystem grouping and whole-file clone exclusion are not
proof of zero leakage. Independent unseen-project challenges remain necessary
when making broader model-quality claims.

## Gold quality gates and audited legacy corrections

The earlier Go labeler omitted `~` from its operator mapping. Preparation repairs
only uncovered `~` characters as `operator`, retaining the existing audit count.

A second omission concerns `switch value := input.(type)`. Go's `types.Info.Defs`
does not associate that declaration identifier with one object: the individual
case clauses introduce separate objects. The Gold labeler now explicitly visits
`ast.TypeSwitchStmt` and labels the guard identifier `variable + declaration`.
Case-body references keep their existing local semantic roles. This also handles
initializers, nested switches, shadowing, Unicode names, and multiple-type cases.
An expression switch, an ordinary type assertion, a blank identifier, or text
inside a comment/string must not be mistaken for this declaration.

Old JSONL records do not require expensive package rechecking. On an incomplete
record, preparation can query `labeling/cmd/nsh-go-syntax-repair`, a streaming
Go parser helper. It reports only AST-confirmed type-switch declarations. The
builder adds only completely uncovered identifier spans and rejects conflicting
existing labels. It never guesses labels for unresolved selectors or other gaps.
The helper does not import corpus packages, resolve dependencies, run source
programs, or download corpora. Its production sources, module file, and pinned
toolchain are included in the snapshot identity.

Repairs exist only in the new prepared snapshot and are recorded in `goldRepairs`
and per-corpus statistics. The report distinguishes repaired declarations from
whole documents recovered after the completeness check. A repaired document may
still be quarantined if another unresolved region remains. Original JSONL files
and previous prepared snapshots are never overwritten.

Any remaining unlabeled non-whitespace region is not silently taught as `outside`.
The document goes to `quarantine.jsonl`, with corpus, package, path, and reason,
and contributes no training or evaluation windows. Other structural errors fail
the build. Legacy standard-library Gold remains best-effort; these local repairs
do not repair its dependency importer or certify all type information as strict.
Its provenance remains explicitly marked `legacy-stdlib`.

After applying a builder-only repair, run only:

```bash
make check
make dataset-go-prepare
```

No standard-library, official-module, application-module, or focused-corpus
collection/relabeling command is needed. Review the new ratios, recovered-document
count, copy exclusions, and remaining quarantine before starting a baseline run.

## Byte encoding and window policy

Training windows use a contiguous Gold-adaptive cursor, without fixed overlap.
A tentative cut is snapped to a UTF-8 character boundary and, where possible,
moved left to the beginning of a semantic span. The next window starts at the
actual cut. Overlong spans may necessarily continue into the next window; these
cases are counted and keep their original `inside` labels. No fake beginning is
inserted just because a window starts there.

Validation and test windows use a character-safe fixed cursor, without consulting
Gold span boundaries. Their window positions cannot benefit from the answer key.
Whole-document sources and UTF-16 Gold are also retained for later document-level
inference evaluation. Evaluation window metrics alone are not a document-level
semantic highlighter benchmark.

The context remains 512 UTF-8 bytes. Each binary row has 512 positions:

- `input_ids.bin`: little-endian unsigned 16-bit byte ids; padding id 256.
- `boundary_labels.bin`: signed 8-bit outside/begin/inside labels 0/1/2.
- `token_type_labels.bin`: little-endian signed 16-bit ids in Go schema order.
- `modifier_bits.bin`: little-endian unsigned 16-bit bitsets in modifier order.

Padding and UTF-8 continuation bytes use label -100. Only character starts receive
boundary/type supervision. Modifier bits are supervised only at span beginnings.
The memory-mapped reader exposes separate attention, label, and modifier masks.
A trainer must not apply modifier loss to every byte indiscriminately.

Natural and focused windows carry separate stream metadata; this stage does not
replicate or oversample focused windows. The Go training loop interleaves
these streams without treating held-out examples as training data. Public
`HighlightResult` offsets remain UTF-16; training byte offsets are internal.

## External outputs

```text
go/
  sample.json
  labeled-sample.jsonl
  corpora/
    gin/
    gorm/
    x-sync/
    ...
  curricula/
    modern-v2r1/
      sample.json
      labeled-sample.jsonl
    targeted-real-v2/
      sample.json
      labeled-sample.jsonl
  prepared/
    current.json
    <snapshot-id>/
      manifest.json
      quarantine.jsonl
      cross-group-copies.jsonl
      split-groups.json
      train/
        documents.jsonl
        windows.jsonl
        input_ids.bin
        boundary_labels.bin
        token_type_labels.bin
        modifier_bits.bin
      validation/
        ...
      test/
        ...
```

The root defaults to `~/Datasets/neural-semantic-highlighting/go`.
`NSH_DATASET_ROOT` overrides its parent, matching the existing corpus pipeline.
Prepared snapshots include input hashes, builder hashes, schema order, split
policy, actual counts, repair/quarantine totals, missing-role reports, and output
checksums. Completed snapshots are immutable. Reruns verify and reuse identical
snapshots; changed inputs create another snapshot without deleting old data.
A small `current.json` pointer is updated only after successful publication.

The temporary SQLite index and partial outputs are removed after completion or
ordinary failure. An exclusive `.prepare.lock` prevents concurrent builders.
After a hard kill, remove a stale lock only after confirming no builder is active.
Do not delete corpus source locks or historical artifacts as a routine retry.

## Verification

`make check` runs the focused Go tests, Python data tests, and CPU-only PyTorch
trainer regressions. The data tests remain independent of an accelerator.
The tests cover the existing Gold fixture offsets, Unicode/CRLF, masks, long-span
progress, evaluation without Gold cuts, duplicates, grouped split conflicts,
quarantine, missing inputs, corrupted columns, replay, and memory-mapped reads.
Regression tests also cover intact-source balancing, shared-copy bridge removal,
focused split conflicts, guarded AST repair, and failed-publication safety.
They do not download Gin or GORM. Full Go tests require the unchanged pinned
Go 1.27.1 toolchain and do not skip newer language fixtures.

## References

- [Go 1.18 release notes](https://go.dev/doc/go1.18)
- [Go 1.20 release notes](https://go.dev/doc/go1.20)
- [Go 1.21 release notes](https://go.dev/doc/go1.21)
- [Go 1.22 release notes](https://go.dev/doc/go1.22)
- [Go 1.23 release notes](https://go.dev/doc/go1.23)
- [Go 1.24 release notes](https://go.dev/doc/go1.24)
- [Go 1.26 release notes](https://go.dev/doc/go1.26)
- [Go 1.27 release notes](https://go.dev/doc/go1.27)
- [Go type-checker information](https://pkg.go.dev/go/types#Info)
- [Go module reference](https://go.dev/ref/mod)

Targeted mined training examples that collide with held-out focused near-copy fingerprints are excluded during preparation and recorded in `focused-near-copy-exclusions.jsonl`; synthetic split collisions remain fatal.
