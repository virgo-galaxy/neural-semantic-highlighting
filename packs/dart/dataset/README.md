# Dart dataset

External root: ~/Datasets/neural-semantic-highlighting/dart; full runs:
artifacts/dart. Previous corpora, experiments and models are preserved.

upstreams.json pins Git revisions and original file blobs/licenses for 80
official Dart core-package files, 60 HTTP-package files and 72 Flutter stable
files. Only source text and license material are captured. Imports, build scripts
and generators never run. Package/module families stay intact. The 55 authored
task families have distinct directory groups; Golden/Playground are denied roots.

make dataset-dart-tools builds the pinned independent C grammar using existing
Clang in ignored project cache. make dataset-dart captures sources, generates
bounded tasks, labels original UTF-16, validates coverage, audits copies and
prepares immutable 512-byte snapshots. Unsupported syntax is quarantined without
fallback. Freeze split-groups.json before the first run; keep natural, focus and
visible-development evidence separate. No compiler-validity claim is made.
