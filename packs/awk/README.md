# AWK pack

One AWK entry covers common AWK/GNU AWK source through the existing small
Transformer, local Python process, UTF-16 spans, renderer and themes. Offline
Gold uses pinned isolated lexer assets, without installing an AWK environment or
executing source. Read [SEMANTICS.md](SEMANTICS.md) for the role contract.

Original source/Gold/prepared snapshots stay external under
`~/Datasets/neural-semantic-highlighting/awk`; full resumable checkpoints stay
under `artifacts/awk`. Selected `model/model.pt` is inference-only. Golden and
Playground remain outside collection. Preserve existing data, models and
experiments. The repository remains private.

The [selected model](model/README.md) and four Playground examples are available.
First natural/focus exact-span test F1 is 96.89%/99.87%. Regex span fragmentation
and advanced GNU call roles remain explicit measured limits.
