# Swift dataset

Use `make dataset-swift`. Original sources and licenses remain under
`~/Datasets/neural-semantic-highlighting/swift`, or `$NSH_DATASET_ROOT/swift`.
Full training runs remain under `artifacts/swift`; neither is committed.

`upstreams.json` pins original Git revisions and every source/license blob.
`fetch_sources.py` captures 238 bounded files from Collections, Algorithms,
Async Algorithms, HTTP Types, Alamofire and Apple's Food Truck SwiftUI sample.
It retains full root license/notice files, byte hashes and capture locks, without
building projects or loading their dependencies. `generate_curriculum.py` writes
68 independently authored task families, 24 variants each, with retained seeds.
`generate_literals.py` adds 12 separate mixed literal/closure families after the
initial validation review, preserving all original tasks and assignments.
Golden, tests and Playground are excluded from collection roots.

The shared collector, fail-closed official parser teacher and validator publish
immutable corpus/Gold snapshots. Preparation audits exact/lexical/normalized
copies across source families before windowing. Freeze `split-groups.json` before
training; future revisions preserve those assignments. Training windows may use
Gold boundaries; validation/test windows do not. Natural, focus and visible
results stay separate. Prior captures and experiments are never overwritten.

The teacher is built from `labeling/SwiftTree.swift` and existing official parser
libraries into content-addressed `artifacts/tools/swift-gold`. Compiler, libraries,
helper source and helper binary hashes are retained. No SDK or package is installed
by these scripts; set `NSH_SWIFT_TOOLCHAIN` to an existing Swift 6.4.2 toolchain.
The existing macOS Command Line Tools supply the SDK/linker for this helper.
