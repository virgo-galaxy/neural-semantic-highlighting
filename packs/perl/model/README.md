# Perl neural model

The selected 894,995-parameter byte Transformer highlights
Perl 5 in the browser Worker or optional native Python runtime. Consumers use:

```ts
const { html } = await highlighter.highlight(source, { language: "perl" });
```

Inference returns original UTF-16 spans without Perl, PPI, compilation, source
regex repairs or command execution. Context remains 512 original UTF-8 bytes;
validated overlapping windows improve long-file edges with additional inference
cost. Browser/Playground consumers require no Python provider or language SDK.

The same exposed four-module cohort improves **83.60% → 91.00%**. The separately
frozen 16-module namespace holdout reaches **88.33%** and remains below the desired
90% floor. Keep both visible. Mixed Here Documents, regex/string boundaries,
references and local role/modifier distinctions remain approximate; see
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

`model.json` records the selected full checkpoint, validation-only averaging,
decoder/window selection and report hashes. The export is inference-only; full
optimizer/RNG checkpoints remain under `artifacts/perl`. Source, Gold, complete
licenses and immutable snapshots stay external under
`~/Datasets/neural-semantic-highlighting/perl`. Additional existing core source is
captured as text without executing modules or installing a Perl environment.

Optional native development/reference output:

```sh
.venv/bin/python -m packs.perl.runtime.local --file example.pl
```

Use `--checkpoint` to inspect compatible full candidates. The preceding model and
its complete original documentation are retained in
[the dated bundle](../model-20261119-v1/README.md). The repository remains private.
