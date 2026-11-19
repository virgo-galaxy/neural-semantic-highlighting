# Selected Makefile model

Common GNU Make source highlighting in one standalone browser/local model.
The same exposed 17-file legacy cohort reaches **94.12%**.
The historical additional 16-file cohort reaches **94.57%** separately.
The selected window revision retains the original neural weights and decoder,
including all 26 previously exact Golden cases.

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

## Reviewed quality revision (2026-11-19)

The current native/browser selection, separate corpus and Golden results,
remaining limits and preserved preceding bundle are recorded in
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
