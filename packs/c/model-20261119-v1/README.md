# C neural model

A small byte Transformer highlights original `.c` and C `.h` source, including
functions, parameters, typedefs, structs/unions/enums, pointers, callbacks, fields,
macros, directives, comments, strings and labels. C++ is a separate pack; header
files here are explicitly treated as C. The pinned grammar targets common C11/C17
and accepted modern/GNU forms, without certifying every C23 or compiler extension.

```js
const { html } = await highlighter.highlight(source, { language: "c" });
```

Browser inference uses float32 ONNX in the existing Worker. No Python process,
compiler, SDK, header lookup, macro expansion or source parser is required.
For local development: `.venv/bin/python -m packs.c.runtime.local --file example.c`.

See [BENCHMARKS.md](BENCHMARKS.md) for measured evidence and
[KNOWN_ISSUES.md](KNOWN_ISSUES.md) for remaining limits. The selected `.pt` is
inference-only; resume full training checkpoints under ignored `artifacts/c`.
