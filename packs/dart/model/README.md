# Dart neural model

Original .dart source: null-safe functions/classes, constructors/generics,
enums/mixins/extensions, async/generators, records/patterns, collections and
plain/raw/multiline/interpolated strings. Common Flutter widget code shares
the same Dart model. Bounded accepted modern syntax is not SDK certification.

    const { html } = await highlighter.highlight(source, { language: "dart" });

Selective import: @nsh/highlighter/languages/dart. Frontend inference needs no
Dart/Flutter SDK, analyzer, Python provider or language parser. Development and
training also use no Dart SDK; the independent pinned CST is supervision only.
Local reference: .venv/bin/python -m packs.dart.runtime.local --file example.dart.

[Evaluation](BENCHMARKS.md) separates natural, focus and visible evidence;
[known issues](KNOWN_ISSUES.md) retain measured limitations. Selected .pt is
inference-only; resumable full checkpoints remain under artifacts/dart.
Previous models, data snapshots, experiments and licenses are preserved.
