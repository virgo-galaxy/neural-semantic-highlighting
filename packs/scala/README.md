# Scala pack

Common Scala 2/3 source, `.scala`, `.sc` and `.sbt`: classes/traits/objects,
functions/methods, generics, patterns, collections, closures, given/using,
extensions, enums, significant indentation, annotations and interpolated strings.

See [semantics](SEMANTICS.md), [dataset](dataset/README.md), [Golden](fixtures/README.md)
and [training](../../training/scala/README.md). Offline Gold uses pinned
[tree-sitter-scala](https://github.com/tree-sitter/tree-sitter-scala) without a
Scala SDK or compiler. [Scala 3 syntax](https://docs.scala-lang.org/scala3/reference/)
is source-local and bounded by the grammar, not certified compiler/type semantics.
