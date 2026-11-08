# SQL pack

One SQL entry covers common PostgreSQL/psql, MySQL and Oracle/SQL*Plus source.
It reuses the existing small Transformer, local process, UTF-16 span protocol,
renderer and themes. Offline Gold reads pinned source without installing a
client/server or executing SQL. Read [SEMANTICS.md](SEMANTICS.md) for role limits.

Original source/Gold/prepared snapshots stay external under
`~/Datasets/neural-semantic-highlighting/sql`; full resumable checkpoints stay
under `artifacts/sql`. Selected `model/model.pt` is inference-only. Golden and
Playground remain outside collection. Preserve all existing data, formal models
and historical experiments. The repository remains private.
