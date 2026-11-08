# CSS family data pipeline

Fetch the explicitly pinned style-source packages once, then run the local
pipeline from the repository root:

```bash
make dataset-css-sources
make dataset-css
```

This runs collection, labeling, independent structural validation and Python
preparation in order. Individual targets are `dataset-css-collect`,
`dataset-css-label`, `dataset-css-validate` and `dataset-css-prepare`.
`test-training-data-css` verifies encoding, cursor windows, copy exclusion,
grouped splits, immutable replay and corruption detection.

## Sources and storage

`sources.json` is the explicit local source allowlist. Missing configured roots
fail collection. Only `.css`, `.scss` and `.less` are considered. Dependencies,
build outputs, fixture/challenge directories, minified CSS and files over 100 KB
are excluded. No source is executed or compiled. Collecting source records does
not claim that the full preprocessor project can be compiled.
The Playground allowlist includes only its application style directories;
highlighter demonstration sources are excluded from collection.

The shared parent defaults to `~/Datasets/neural-semantic-highlighting` and can
be overridden with `NSH_DATASET_ROOT`. This pack appends `/css`:

```text
css/
  current-corpus.json
  corpora/<snapshot>/
    sample.json
    sources.jsonl
    exclusions.jsonl
  current-gold.json
  gold/<snapshot>/
    sample.json
    labeled-sample.jsonl
    quarantine.jsonl
  prepared/
    current.json
    <snapshot>/
      manifest.json
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

Corpora capture original source bytes in JSONL. Labeling reads those captured
bytes, not a changing checkout. Failed parsing is retained in quarantine with
its source identity. Gold snapshots bind the original corpus, labeler, locked
dependencies and schema; prepared snapshots bind Gold, builder code and seed.
Existing completed snapshots are verified and reused, never rewritten. Pointers
are updated only after successful publication. Interrupted jobs retain earlier
completed snapshots; inspect a stale lock's owner before removing the lock.

## Splits and windows

Identical-source Gold conflicts stop preparation. Exact copies are deduplicated;
copies with identical lexical or normalized shapes across source directories are
excluded and audited. Remaining source directories are assigned intact to
train/validation/test, targeting 80/10/10 while balancing all three document kinds.
Every kind must have at least three independent groups and nonempty holdouts.
The corpus can contain checked-in examples and integration sources; "natural"
means real collected source, not exclusively production application code.

Grouping happens before windows. Training uses Gold-adaptive semantic cuts;
validation/test cuts are fixed and Unicode-safe without Gold boundaries. Every
public span uses UTF-16; internal labels use UTF-8 character-start bytes. Padding
and continuation bytes are ignored, and modifiers are supervised only at BEGIN.

Initial local corpora are useful for pipeline checks but may lack important Sass
and Less roles. Inspect per-kind role support before choosing a training budget.
Do not treat absent classes, a successful data pipeline or a smoke checkpoint as
evidence of production model quality. Keep final held-out testing independent of
iterative validation and real-source diagnostics.

## Pinned supplementary sources

`packages.json` pins Bootstrap 5.3.8, Bulma 1.0.4 and Pico 2.1.1 SCSS, plus Ant
Design 4.24.16 Less. Pico was added after real Grid code exposed missing `auto-fit`
and `minmax` training coverage. `dataset-css-sources` downloads only these explicit npm archives,
verifies SHA-512 registry integrity and keeps the selected original style files,
license files and `source.lock.json` under the external CSS dataset. It uses
normal system TLS validation through curl. It performs no npm installation or
source execution. Existing locked sources are checked and reused; modified sources
fail. The collector verifies source file hashes against those locks.
