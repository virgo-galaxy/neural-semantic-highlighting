# Java

One Java entry for `.java` source, including package/module descriptors, traditional
classes and modern records, sealed types, lambdas, annotations, generics, pattern
matching and text blocks. Offline Gold covers non-preview syntax through JDK 22;
future/preview features are not certified. Version numbers do not split the model.

The selected neural model uses original UTF-8 bytes and returns original UTF-16
semantic spans. Local and browser inference require no JDK or source parser.
[SEMANTICS.md](SEMANTICS.md) describes local roles, lexical scope and boundaries.
[Training](../../training/java/README.md) preserves the existing data/checkpoint
locations, short experiments and matching-test promotion process.

The selected baseline and first independent test are documented in
[model/README.md](model/README.md), [BENCHMARKS.md](model/BENCHMARKS.md) and
[KNOWN_ISSUES.md](model/KNOWN_ISSUES.md). Java is available through the public
`@nsh/highlighter` browser API and the Playground, using the existing theme presets.
