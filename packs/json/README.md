# JSON / JSONC pack

One independent JSON-family model, two explicit source entries: `json` and `jsonc`.
JSON is strict; JSONC includes comments and common trailing-comma configurations.
JSON5 extensions and schema/type validation are outside this pack. Frontend and
Playground inference run in the existing browser Worker without a parser or Python.

See [semantics](SEMANTICS.md), [dataset](dataset/README.md), [Golden](fixtures/README.md),
[training](../../training/json/README.md) and [consumer usage](../../README.md).
No new SDK or global package is installed. Keep the established independent-pack,
external-data, full-checkpoint and short English commit workflow.
