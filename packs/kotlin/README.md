# Kotlin pack

Original `.kt` and `.kts` source, including common coroutines, Compose and Kotlin
build-script syntax. Classes/interfaces/objects, generics, nullable/pattern code,
lambdas, properties/delegates, annotations and string templates share one model.
Offline code/script profiles retain separate evaluation without splitting the
public Kotlin entry.

See [scope](SEMANTICS.md), [dataset](dataset/README.md), [independent Golden](fixtures/README.md)
and [training](../../training/kotlin/README.md). Official Kotlin 2.4.21 PSI/lexer
components run only in isolated development cache on the existing JDK 22. No
Kotlin SDK, Gradle or Android environment is installed. Collected source, scripts,
annotations, plugins and build files are never executed or typechecked.
Modern syntax is bounded by the [official release](https://github.com/JetBrains/kotlin/releases/tag/v2.4.21)
and parser; this is source-local supervision, not project analysis.
