# Selected Makefile model

Common GNU Make source highlighting in one standalone browser/local model.
Fresh independent exact-span F1 is **93.79% on 16 new files**.
On the same exposed 17-file legacy cohort, F1 improves **89.14% → 92.87%**.

```ts
const { html } = await highlighter.highlight(source, { language: "makefile" });
```

The public API, aliases, themes and one-model selective import remain unchanged.
`makefile`, `make`, `mk`, `mak`, `gnumake` and `gnumakefile` share one descriptor;
use `@nsh/highlighter/languages/makefile`. Browser/Playground need no Make, SDK,
Python or source parser. Markdown can reuse an explicitly registered model in
predicted Makefile fences. All output preserves original source and offsets.

The model retains four layers, width 128, and 512 UTF-8 bytes of context, with
**894,479 parameters** (768 more than v1). A learned five-byte residual and
existing train-fitted joint BIO decoder improve real-source boundaries. No
source-spelling/regex/parser repair is added. Old
[native](../model-20261118-v1/ARCHIVE.md) and
[browser](../browser-20261118-v1/ARCHIVE.md) bundles remain intact.
See [evaluation](BENCHMARKS.md), [known limits](KNOWN_ISSUES.md) and
[semantics](../SEMANTICS.md). Continue training only from complete artifacts
checkpoints. Repository/packages remain private; no npm publication occurs.
