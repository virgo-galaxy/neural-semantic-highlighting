# Dart pack

Original .dart source, including common Flutter widget composition. Null safety,
generics, classes/enums/mixins/extensions, async/generators, collections, strings
and bounded modern record/pattern/constructor forms share one entry.

See [contract](SEMANTICS.md), [dataset](dataset/README.md),
[Golden](fixtures/README.md) and [training](../../training/dart/README.md).
No Dart/Flutter SDK is installed for supervision, training or frontend inference.
Offline CST labels are source-local approximations, not analyzer type checking.

Modern syntax is checked against the [Dart language documentation](https://dart.dev/language)
and the pinned [independent grammar](https://github.com/nielsenko/tree-sitter-dart/tree/cc75f92b34037bcdbc05b12b0db7fe20677306c1).

The selected [model](model/README.md) is available through `language: "dart"`
and `@nsh/highlighter/languages/dart`. [Evaluation](model/BENCHMARKS.md) records
94.22% natural test exact-span F1 over 20 files and separates the visible probes.
[Known issues](model/KNOWN_ISSUES.md) retain literal, constructor and local-role
limitations. Resumable full checkpoints stay under `artifacts/dart`.
