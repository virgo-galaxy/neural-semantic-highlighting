# XML / SVG neural model

UTF-8 XML 1.0 and SVG source, qualified tags/attributes, text, references, declarations, comments and opaque CDATA.

```ts
const { html } = await highlighter.highlight(source, { language: "xml" });
```

XML and SVG retain distinct document kinds. languages/svg re-exports languages/xml; importing either or both shares one model asset. Select the language explicitly; filename/content auto-detection is not provided.
Selective import: `@nsh/highlighter/languages/xml`. Case-normalized IDs share one
model. Browser/Playground consumers require no language SDK, interpreter/compiler,
parser, dependency environment or Python process. Offline Gold uses Existing CPython 3.12 Expat raw-event and namespace-aware validation with binary/source hashes; no downloads, SDKs or packages.
Collected projects and dependencies never execute or typecheck.

[Evaluation](BENCHMARKS.md) separates natural, focus and visible evidence;
[known limits](KNOWN_ISSUES.md) retain measured errors and source-local scope.
Selected .pt/ONNX are inference-only. Resume full artifacts/xml checkpoints only.
All previous data, experiments and formal models remain preserved.

Use `{ language: "svg" }` for SVG. The selective `languages/svg` export is the
same descriptor as `languages/xml`; both kinds retain their name but share one
asset and inference weights. [Separate XML/SVG test results](BENCHMARKS.md) are
87.72% on seven XML files and 100% on six SVG files; the small SVG sample is not a
universal guarantee. Neither kind executes XML/SVG, external DTDs or code bodies.

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
