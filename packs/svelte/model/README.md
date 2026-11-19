# Svelte neural model

Original `.svelte` components: markup, comments/entities, interpolation,
if/each/await/key blocks, snippets/render, ordinary and directive attributes,
legacy exports/reactivity/events/slots, Svelte 5 runes and instance/module scripts.
The offline parser is pinned to Svelte 5.38.0; highlighting is not compiler-version
validation or a claim of every future Svelte feature.

```js
const { html } = await highlighter.highlight(source, { language: "svelte" });
```

Selective `@nsh/highlighter/languages/svelte` includes existing JS/TS and
CSS/SCSS/Less models. It uses predicted regions and a fixed TS expression wrapper,
without parsing or executing source at runtime. Whole attribute values remain
opaque by contract; Tailwind classes need no separate language model.

No Svelte runtime/SDK, preprocessor, Python provider or highlighting server is
required by consumers. The Gold-only official compiler bundle uses existing Node
and lives in ignored cache; no npm dependency, global package or lockfile change
was introduced. Base-only local reference:
`.venv/bin/python -m packs.svelte.runtime.local --file Component.svelte`.

[Evidence](BENCHMARKS.md) separates natural/focus/base/composed scores.
[Known issues](KNOWN_ISSUES.md) record controlled limits. Selected `.pt` is
inference-only; resumable checkpoints stay under `artifacts/svelte`.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
