# Scala dataset

Use `make dataset-scala`. Source, original licenses and immutable snapshots stay
under ~/Datasets/neural-semantic-highlighting/scala; full optimizer/RNG checkpoints
remain under artifacts/scala. Inference bundles contain neither raw data nor
resumable checkpoints. Golden/tests/Playground never enter training capture.

Five pinned upstream captures contain 180 Scala files from Scala 2 standard library,
Scala 3 library, Cats, Ox and Kyo. The 24 Kyo files form one complete project
family reserved for the unseen Scala 3 test before any neural evaluation. The
shared collector excludes 21 captured files (including one Kyo source) in reserved paths, retaining
all originals. Original Git blobs and root licenses/notices are
preserved. The original curriculum adds 54 families with 24 variants each, covering
common Scala 2 braces, Scala 3 indentation/contextual forms and mixed string code.
Copy audits precede windowing; source families freeze before training, natural and
focus windows remain separate, and future revisions retain old assignments.

Pinned parser/runtime sources compile with existing Clang only in ignored project
cache. No Scala SDK, sbt, global package or additional toolchain is installed.
Collected projects, macros, compiler plugins, scripts and dependencies never run.
Unknown syntax, parser errors and original Unicode/coverage errors fail closed;
quarantines remain explicit rather than silently fixing original source.
