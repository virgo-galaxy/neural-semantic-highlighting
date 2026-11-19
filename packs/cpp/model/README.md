# C++ neural model

A small byte Transformer highlights original C++ source and explicit C++ headers:
classes, constructors/destructors, methods/fields, templates, namespaces,
lambdas, structured bindings, pointers, standard-library forms, concepts/requires,
macros and literals. Targets common C++11–20 and accepted modern syntax; it does
not certify every C++23/26 feature or project/type system.

```js
const { html } = await highlighter.highlight(source, { language: "cpp" });
// "c++" and "cxx" share the same model.
```

Use `@nsh/highlighter/languages/cpp` for selective registration. `.h` filenames
remain C by default; pass `cpp` explicitly for C++ header contents. No compiler,
SDK, Python process, header resolver, macro expander or parser is used in browser
inference. Local development: `.venv/bin/python -m packs.cpp.runtime.local --file example.cpp`.

See [BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
The selected `.pt` is inference-only; resume complete checkpoints under
`artifacts/cpp`. Previous datasets, experiments and C/other models are preserved.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
