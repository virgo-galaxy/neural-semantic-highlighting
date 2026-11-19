# Zig neural model

Original `.zig` source targeting **Zig 0.17.1 only**: functions, containers,
errors/optionals, captures, comptime/generics, builtins, current standard-library
usage, strings/comments and source-local name roles. Historical versions and
master snapshots are not compatibility targets. ZON is a separate file format.

```js
const { html } = await highlighter.highlight(source, { language: "zig" });
```

Selective import: `@nsh/highlighter/languages/zig`. Browser/Playground inference
requires no Zig SDK, compiler, Python provider or language parser. The host SDK
upgrade is only for development checks. Local reference:
`.venv/bin/python -m packs.zig.runtime.local --file example.zig`.

[Evaluation](BENCHMARKS.md) separates natural, focus and visible development
evidence. [Known issues](KNOWN_ISSUES.md) record quoted identifiers, literal
boundaries and approximate local roles. Selected `.pt` is inference-only;
resumable full checkpoints stay under `artifacts/zig`. All earlier data,
experiments and selected models are preserved.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
