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
make dataset-go-curriculum
```

Do not rerun standard-library or official-module collection merely to publish a
new prepared snapshot. Existing immutable Gold corpora are reused. The
application command adds the explicitly selected Gin and GORM module sources.
`dataset-go-curriculum` builds the targeted real-source focused corpus, generates
the integrated synthetic curriculum, then runs preparation.

`training/go/corpora.json` explicitly selects the standard library, seven official
modules, two application-framework modules, `curricula/modern`, and
`curricula/targeted-real`. Missing sources cause a clear error instead of silently
creating a smaller dataset.

## Canonical focused curriculum

The generator lives in `packs/go/dataset/curriculum_templates.go`. It is one
integrated capability matrix: 131 structural families across 14 feature groups.
The canonical generator uses 16 variants per family, producing 2,096 synthetic
documents while keeping structural diversity and renamed/value variants as
separate concepts.

The capability set covers generic functions, comparable/array behavior, built-ins,
integer range, range-over-function, generic aliases, expression-valued `new`,
self-referential constraints, generic methods, promoted-field literals, generalized
function inference, struct tags, general string robustness, and low-frequency core
semantics. Every feature has explicit train/validation/test families; higher-risk
features have additional train structures and hard negatives.

Every generated document is formatted and strictly type-checked by the pinned Go
toolchain. No generated program is executed. The curriculum does not add
feature-specific public token types: tags and ordinary literals remain `string`,
while comments/directives remain `comment`.

## Targeted real-source mining

The targeted miner downloads only modules listed in
`packs/go/dataset/sources/targeted.json`, runs the existing strict Gold pipeline,
and retains files with source structures that can be detected without identifier
name guesses or executing code. These records are train-only. Validation and test
remain structurally independent synthetic families.

The canonical focused outputs are:

```text
curricula/modern
curricula/targeted-real
```

Targeted mined examples that collide with held-out focused near-copy fingerprints
are excluded during preparation and recorded in
`focused-near-copy-exclusions.jsonl`; synthetic split collisions remain fatal.

## Final from-scratch training

After the canonical dataset, model, loss, sampler, and quality gates are frozen,
start the formal run with:

```bash
make train-go-final
```

This command starts from random initialization, trains the complete curriculum,
uses confusion-aware focused sampling and lexical validation, and selects
checkpoints with the quality-gated policy. A prior diagnostic checkpoint can stay
protected outside the pipeline as a baseline, but it is not an initialization
source for the formal run.

The quality gate requires aggregate natural/focused performance, every sufficiently
supported natural role, and all targeted semantic capabilities to pass before an
epoch is eligible for `best.pt`. Among eligible epochs, selection remains based on
natural whole-document exact-span F1.

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

Natural and focused windows carry separate stream metadata. Preparation does not
replicate focused windows. During training, focused windows retain their feature/family metadata. Generic
runs may use feature-balanced sampling; the formal run uses confusion-aware
sampling so broad capability coverage and semantic contrast lanes both receive
budget without naming a one-off patch feature. Held-out examples are never
sampled for optimization. Resume preserves the schedule saved by that run.
Public `HighlightResult` offsets remain UTF-16; training byte offsets are internal.

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
    modern/
      sample.json
      labeled-sample.jsonl
    targeted-real/
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
