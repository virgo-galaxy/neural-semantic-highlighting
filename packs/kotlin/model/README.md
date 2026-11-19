# Kotlin neural model

Original `.kt` and `.kts` source, common coroutine/Flow and Jetpack Compose syntax,
Gradle Kotlin scripts, classes/objects, generics, nullable code, lambdas,
properties/delegates, annotations and string templates share one model.

```ts
const { html } = await highlighter.highlight(source, { language: "kotlin" });
```

Aliases: `kt`, `kts`, `kotlin-script`; IDs are case-insensitive. Selective import:
`@nsh/highlighter/languages/kotlin`. Browser/Playground consumers require no JDK,
Kotlin SDK, Gradle, Android SDK, parser or Python process. Local reference:
`.venv/bin/python -m packs.kotlin.runtime.local --file example.kt`.

Offline Gold uses official Kotlin 2.4.21 PSI/lexer components from an isolated
project cache on the existing JDK 22.0.1. It does not resolve dependencies,
typecheck collected projects, run scripts or load compiler plugins.
[Evaluation](BENCHMARKS.md) separates natural/focus/visible evidence;
[known issues](KNOWN_ISSUES.md) retain measured literal and source-local role limits.
Selected .pt/ONNX are inference-only. Resume full artifacts/kotlin checkpoints.
All previous datasets, experiments and formal models remain preserved.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
