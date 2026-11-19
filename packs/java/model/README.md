# Java neural model

A small byte Transformer highlights Java `.java` source, package/module descriptors,
classes/interfaces/enums, annotations, generics, lambdas, records, sealed types,
pattern matching and text blocks. The offline corpus covers ordinary Java 8–22 and
non-preview modern syntax through the available JDK 22. Version numbers share one
model; later/preview features are not certified.

The frontend highlighter runs the selected float32 ONNX weights in its existing
browser Worker. Consumers need no JDK, Python process or project dependencies.

```js
const { html } = await highlighter.highlight(source, { language: "java" });
```

Local neural inference is also available for development:

```sh
.venv/bin/python -m packs.java.runtime.local --file Example.java
```

Read [BENCHMARKS.md](BENCHMARKS.md) for the exact parameter count, bounded training
history, natural/focus evidence and first independent test. Read
[KNOWN_ISSUES.md](KNOWN_ISSUES.md) for source-display limits. The model describes
source-local roles; it is not a Java compiler or full symbol resolver.

Inference consumes only original text and learned weights. There is no parser,
Gold teacher, regular-expression source repair, SDK invocation or source execution.
The float32 `.pt` artifact is inference-only. Training continues only from complete
checkpoints under `artifacts/java`, preserving original data and historical runs.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
