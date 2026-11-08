# PowerShell semantic contract

One PowerShell entry covers common Windows PowerShell 5.1 and modern PowerShell
script/module syntax (`.ps1`, `.psm1`, `.psd1`). This is source display coverage,
not execution compatibility with every version, module, host or .NET platform.
There is one offline coverage profile; inference receives original source and
`powershell`, with no version/environment detection or native PowerShell parser.

Pinned isolated Pygments supplies offline lexer machinery, extended with a
bounded original-coordinate display grammar. It never imports modules, resolves
.NET types, starts pwsh or executes input. Reserved/control words are `keyword`;
variables include scoped/environment/braced/automatic names. Visible assignments
and param declarations add `declaration`; known automatic names add default-library.
Bracketed type expressions are whole `type` spans; class/enum names are declarations.

Visible function/filter names are function declarations. Verb-noun command names
are function-like; names not visibly defined get an approximate default-library
flag, without a module lookup. Member names are properties, call-like members are
functions, dash arguments are parameters and bare command arguments are string-like.
Hashtable keys use property. These roles are lexical/source-local and approximate:
assignment/member scope, aliases, custom commands and attribute arguments are not
resolved through an interpreter.

Quoted strings and both forms of Here-String are opaque whole strings, including
interpolation spelling. No JS, JSON, SQL or PowerShell sublanguage is composed
inside their bodies. Closing Here-String markers begin a physical line. Original
CRLF/Unicode remain unchanged. Nested block comments are coalesced offline;
neural canonical coalescence merges touching predicted comment ranges only.
Modifiers use predicted roles, never source regex repairs or Gold boundaries.
Numbers, operators and punctuation have direct roles, including modern ??/??=,
?. and pipeline-chain spellings. Complex interpolation and grammar remain bounded.

Every non-whitespace source character is covered once; offsets are original UTF-16.
Invalid teacher output is quarantined. Golden and Playground are excluded from
collection. Natural source directories and original task families split before
windows with exact/lexical/normalized copy checks and frozen assignments. Report
natural and focused results separately. Model context remains 512 UTF-8 bytes.
