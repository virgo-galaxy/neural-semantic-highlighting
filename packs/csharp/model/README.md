# C# neural model

A small byte Transformer highlights original `.cs` source with classes, structs,
interfaces/enums, methods/properties, attributes, generics, records, async/await,
Lambda, LINQ, patterns and modern strings. The pinned offline grammar provides
bounded source-local Gold, not full Roslyn/project semantics or certification of
every newer/preview language version.

Browser inference uses the selected float32 ONNX weights in the existing Worker.
No .NET SDK, Mono, Python process or offline parser is needed by a consumer.

```js
const { html } = await highlighter.highlight(source, { language: "csharp" });
// "cs" and "c#" are aliases of the same model.
```

Local neural inference is also available for development:

```sh
.venv/bin/python -m packs.csharp.runtime.local --file Example.cs
```

See [BENCHMARKS.md](BENCHMARKS.md) for independent test evidence and bounded training;
read [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for measured role/pattern/string limits.
Inference consumes only original text and learned weights, with no compiler,
reflection, regex source repair, source execution or SDK lookup. The `.pt` export
is inference-only; full resumable checkpoints remain under `artifacts/csharp`.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
