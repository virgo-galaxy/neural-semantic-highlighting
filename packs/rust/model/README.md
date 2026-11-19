# Rust neural model

Original `.rs` source: functions/methods, structs/enums/traits/impls, local bindings,
generics/lifetimes, patterns, closures, async/await, modules/imports, attributes and
macro syntax. Common stable 2018/2021/2024 source shares one entry; highlighting
is not compiler-version validation or a claim of every newest/nightly feature.

```js
const { html } = await highlighter.highlight(source, { language: "rust" });
// "rs" uses the same entry.
```

Selective import: `@nsh/highlighter/languages/rust`. Browser/Playground inference
requires no Rust compiler, Cargo, Python process, parser or project environment.
The existing host compiler was updated only for development and authored checks.
Local reference: `.venv/bin/python -m packs.rust.runtime.local --file example.rs`.

[Evaluation](BENCHMARKS.md) keeps natural/focus/visible evidence distinct.
[Known issues](KNOWN_ISSUES.md) include raw/format-string boundaries and local
semantic approximations. Selected `.pt` is inference-only; resumable checkpoints
stay under `artifacts/rust`. Existing models and historical data/runs are preserved.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
