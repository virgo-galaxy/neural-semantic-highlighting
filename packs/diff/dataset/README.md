# Diff/Patch data

Commit/blob-pinned original maintained patches come from production distribution,
dependency-port and application patch roots. They are real build/distribution
artifacts, rather than parser test fixtures. A patch that modifies upstream tests
can still be a genuine maintained dependency patch. Original repository license
and notice files are preserved along with patch headers; no blanket assertion is
made that the repository's own license replaces an upstream patch's notices.

`source-selection.json` freezes whole dependency/port/patch-series families from
metadata before source capture or predictions. Exact, lexical and structural
cross-family copies are excluded by the unchanged shared pipeline. Unsupported
or invalid complete patches are quarantined without changing original content.

External root: `~/Datasets/neural-semantic-highlighting/diff/`. Raw sources,
licenses, original focus curriculum, corpus, Gold and prepared snapshots are
immutable and remain outside Git. Golden/display sources never enter training.
Full optimizer/RNG checkpoints stay under `artifacts/diff`, separate from formal
inference `.pt`/ONNX files.

    make dataset-diff
    make test-labeling-diff

The existing Git executable is a parse-only independent oracle in statistics
mode. No patch is applied, no files or imports are loaded, and no source or hook
runs. No language SDK/global dependency is installed. The repository and package
distribution remain private; no publication or data upload is performed.
