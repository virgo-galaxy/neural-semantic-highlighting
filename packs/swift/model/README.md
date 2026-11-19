# Swift neural model

Original `.swift` source, including common SwiftUI code. Functions, types/protocols,
extensions, generics, enums/patterns, closures, async/actors, attributes/property
wrappers and original strings/regex share one model.

```ts
const { html } = await highlighter.highlight(source, { language: "swift" });
```

Selective import: `@nsh/highlighter/languages/swift`. Browser/Playground inference
requires no Swift, Xcode, language parser or Python process. Local reference:
`.venv/bin/python -m packs.swift.runtime.local --file example.swift`.

Offline Gold uses the already installed official Swift 6.4.2 SwiftParser, with
source-local role approximations and no imports, typechecking, macro expansion
or project execution. [Evaluation](BENCHMARKS.md) separates natural/focus/visible
evidence; [known issues](KNOWN_ISSUES.md) retain measured literal and role limits.
Selected .pt/ONNX are inference-only. Resume full checkpoints under artifacts/swift;
all previous data snapshots, runs and formal models remain preserved.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
