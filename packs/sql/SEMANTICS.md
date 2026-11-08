# SQL semantic contract

One SQL entry covers PostgreSQL/psql, MySQL and Oracle/SQL*Plus source. Profiles
are offline coverage annotations; inference receives source and `sql`, without a
database connection, client, parser, dialect heuristic or source-regex repair.
Offline Gold uses one pinned original-coordinate display lexer and deterministic
local roles. Common syntax has common labels across profiles. Input scripts are
never executed and includes, stored programs or client shell commands never run.

Reserved/control words and client commands use `keyword`; quoted literals and
quoted identifiers use whole `string` spans. Known builtin types are recognized
in declaration/cast positions. Direct call-like words use `function`, with
`default-library` for known builtins unless visibly defined. Function definitions
and known signature parameter names add `declaration`; visible local bindings
use `variable`. Schema-object positions and unquoted qualifiers use `namespace`,
other names use `property`. This is bounded source-local display, without schema,
privilege, import or complete procedural-scope resolution.

PostgreSQL positional/psql/Oracle bind markers use `parameter`; MySQL @ variables
use `variable`. Oracle substitution markers are parameter-like. Operators,
numbers and structural punctuation use direct roles. Named dollar-quoted and
Oracle alternative-quoted strings are opaque; no embedded language is executed
or composed. MySQL delimiter scripts keep their unquoted body SQL tokens.
Quoted identifiers share string-like display across dialects to avoid conflicting
labels for the same isolated source. Ambiguous dialect-specific semantics remain
bounded coverage, not execution compatibility with every engine/version.

psql backslash commands (including `\dt`) and MySQL/SQL*Plus directives preserve
original ranges. Their textual arguments use string regions, without following
paths or connecting to a service. Block comments merge touching lexer fragments;
line-ending gaps remain outside. Neural comment coalescence and modifier-role
masks use predicted ranges/roles only, never source spelling or Gold boundaries.

UTF-16 offsets preserve original CRLF, Unicode and tabs with complete non-whitespace
coverage, no overlap and original token checks. Unknown tokens are quarantined.
Golden and Playground stay outside collection. Related source/task families and
normalized copies split before windows, retaining frozen assignments. Report
natural/focused evidence per coverage profile; context remains 512 UTF-8 bytes.
