# Dockerfile dataset

Data stays under `~/Datasets/neural-semantic-highlighting/dockerfile`; artifacts
and complete training checkpoints stay under `artifacts/dockerfile`. Existing
public Git tree inventories provide a bounded 70 original candidates at their
already pinned revisions, with original Git blobs and applicable licenses.
No old dataset, clone, experiment or formal model is modified. Filename selection
and complete related-family holdouts are fixed before source parsing/training.
A JavaScript highlighter module whose filename resembles Dockerfile is rejected
by the official Dockerfile parser; its original bytes remain quarantined.

The independent structural oracle is official BuildKit v0.35.0, compiled with
existing Go in an isolated project cache. The Go toolchain never auto-downloads;
Docker Engine is not installed or needed. Existing pinned Shell and JSON tools
supply offline nested supervision. No source/image/dependency command executes.
Parser/module/compiler/binary hashes, dependency checksums and licenses remain
retained. This is parse-only display supervision, not full container build validation.

24 original structural families have 24 variants each (576 tasks), varying
stage/step counts before literal changes. Families, exact/lexical/structural copy
exclusions and natural/focus streams are separate. Source-local spans preserve
all non-whitespace original UTF-16 characters; unmapped/overlapping input is
quarantined. Corpus, Gold and prepared revisions are immutable. Freeze the full
family map before training. Never select from independent test predictions;
stop training before the first adaptive test of a frozen candidate. Golden and
Playground never enter collection roots. See source-selection and split-groups.

The frozen retained natural splits are **39 / 12 / 14**; authored focus splits
are **456 / 48 / 72**. Two exact duplicates are merged and two cross-family
copy documents are excluded before training. All 83 original natural/focus
family assignments remain recorded; the independent test is never used for
selection. Prepared snapshot: `7241426774990042762de173e11340d3a6b295327696246187d978b8a316fb4e`.
