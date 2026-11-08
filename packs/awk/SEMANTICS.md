# AWK semantic contract

One AWK entry covers common POSIX-style and GNU AWK source. The pinned isolated
Pygments lexer plus a source-local offline adapter labels original source without
executing AWK, loading extensions or following includes. The neural runtime uses
only model predictions, never a lexer, regex repair or source execution.

Reserved/control/phase words and statement forms (`print`, `printf`, `getline`,
`next`, `delete`) use `keyword`. Named function definitions use
`function+declaration`; signature variables use `variable+declaration`. Other
variables are implicit and are not declarations merely because assigned.
Recognized builtin calls/variables use `function`/`variable+default-library`;
source-local function definitions override builtin-name recognition. Unknown
call-like identifiers use `function`, other identifiers use `variable`.

Static/single-word dynamic fields (`$1`, `$NF`, `$name`) are whole variable
spans; computed `$(expression)` keeps its operator/punctuation/expression roles.
Regex and quoted literals are whole `regexp`/`string` regions. Comments, numbers,
operators and structural punctuation use direct roles. GNU phase words,
`@include`/`@load`/`@namespace`, qualified names, typed regex constants and indirect
calls are explicit offline coverage, without loading any files or libraries.
GNU coprocess `|&` and regex expectations across escaped physical newlines are
also recognized offline, retaining the original continuation character.

Ranges use original UTF-16 characters, preserving CRLF, tabs and Unicode.
Complete non-whitespace coverage, no overlap and original lexer text are checked;
unknown tokens are quarantined. This is a bounded lexical/display contract, not
a compiler or promise that every AWK implementation accepts each GNU extension.
Modifier-role masks use predicted roles only. Context is 512 UTF-8 bytes.

Golden and Playground never enter collection. Source/task families and normalized
copies split before windows, preserving frozen assignments across revisions.
Natural-source and focused evidence remain separate, with real-code inspection.
