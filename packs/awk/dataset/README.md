# AWK corpus

A bounded capture selects complete GNU AWK 5.4.1 example/library programs from the
[official source archive](https://ftp.gnu.org/gnu/gawk/gawk-5.4.1.tar.xz), with
archive/file hashes and the complete original GPL license. No AWK code is
compiled, installed or executed. Source bytes remain unchanged.

Original short/mixed programs cover record fields, phases, functions, arrays,
regex, loops, conditionals and common GNU extensions. Related variants share one
task family before windows. Golden and Playground are never collected.

Pinned Pygments 2.21.0 stays in ignored offline tool assets; runtime needs no
native AWK environment. Source, Gold and prepared snapshots stay under the
external `awk` dataset directory, full checkpoints under `artifacts/awk`.
