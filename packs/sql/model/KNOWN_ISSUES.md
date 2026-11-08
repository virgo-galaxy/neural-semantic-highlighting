# SQL measured limits

- **Mixed literal boundaries remain weak.** Short Oracle q-quote Golden cases
  work, but the longer Oracle display probe splits the literal and can mislabel
  the following SELECT tail as comment. PostgreSQL dollar bodies can split and
  expose SQL-like interior tokens instead of staying one opaque string. The
  literal supplement improved held-out development scores without solving these
  combinations. Retain these cases as regression evidence.
- **Client directives depend on context.** Isolated `\\dt`, `\\d+` and `\\set`
  Golden probes work. In a mixed PostgreSQL routine example some leading psql
  command words become string-like. SQL*Plus PROMPT arguments and MySQL closing
  DELIMITER arguments also have boundary/role errors. No client command is run.
- **Names and procedural types are approximate.** Table/alias qualifiers,
  namespace/property distinctions, procedure parameter references, casts and
  declaration/default-library modifiers sometimes disagree with offline Gold.
  Gold itself supplies bounded lexical/local roles, not database schema analysis.
  Oracle DECLARE/INTO names can also receive inconsistent namespace-like Gold.
- **Comments and context are bounded.** Nested comments fragment; long literals,
  procedural blocks and distant definitions can lose state beyond the 512-byte
  context. Dollar-body languages are not recursively highlighted. SQL JSON
  operators are syntax coverage, not a separate JSON pack.
- **Evidence is small and uneven.** PostgreSQL tutorials, MySQL sys-schema
  helpers and Oracle sample schemas are source-family holdouts, not independent
  projects or full engine/version certification. Natural/focus/profile results
  stay separate; read BENCHMARKS.md rather than treating pooled F1 as universal
  accuracy. Future comparisons on the archived first test are known-test results.
