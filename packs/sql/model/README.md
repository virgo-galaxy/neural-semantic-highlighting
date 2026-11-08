# SQL neural model

One small byte Transformer provides one SQL entry for common PostgreSQL/psql,
MySQL and Oracle/SQL*Plus source. It uses the same independent-pack architecture,
original UTF-16 spans, renderer and persistent local bridge as previous models.
No database/client environment was installed. Inference needs no parser or lexer
and never executes SQL, stored code, includes or shell commands.

The selected full checkpoint and measured test results are recorded in
[BENCHMARKS.md](BENCHMARKS.md). Common query/routine highlighting is usable;
mixed special strings, procedural roles and client boundaries retain the explicit
[known limits](KNOWN_ISSUES.md). This is a bounded first baseline.

```sh
.venv/bin/python -m packs.sql.runtime.local --file example.sql
```

Full resumable checkpoints stay under `artifacts/sql`; training transferred full
checkpoints only. The float32 `model.pt` export is inference-only. External source,
Gold and prepared revisions stay under `~/Datasets/neural-semantic-highlighting/sql`.
Preserve all prior datasets, experiments and formal models. Repository stays private.
`NSH_SQL_CHECKPOINT` selects a compatible development checkpoint in Playground.
