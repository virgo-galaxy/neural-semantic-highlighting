# BAT / CMD semantic contract

One BAT / CMD entry covers common modern Windows cmd.exe batch source (`.bat`,
`.cmd`), without installing Windows, launching cmd.exe or executing input.
Legacy COMMAND.COM/Windows version compatibility is not certified. Source is
never imported and includes, subroutines, processes or shell commands never run.

Offline Gold extends pinned isolated Pygments BatchLexer to preserve complete
`%%A` / `%%~nxA` loop-variable spans. Percent/delayed/argument variables are
variable roles; visible unquoted SET bindings and FOR declarations add declaration.
Builtin command/control words use keyword. Source-local labels and references use
function, with declaration on a physical label line. External command positions
are function-like without path resolution; command options use parameter where
recognized. Bare arguments, quotes and escapes are string-like; expanded variable
spans within quotes stay separate. Arithmetic numbers/operators and structural
punctuation keep direct roles. This is bounded lexical display, not macro expansion,
execution order analysis, full command parsing or scope/type resolution.

REM and double-colon comments preserve original text. Touching offline string and
comment fragments coalesce; runtime applies the same canonical policy to touching
predicted ranges/roles only. Whitespace gaps are not bridged. No source regex,
lexer or Gold boundary is consulted during inference. Modifiers use predicted
roles. Caret/escaped command syntax and nested parentheses remain bounded.

Coordinates are original UTF-16 with original UTF-8, CRLF and Unicode retained.
Every non-whitespace character is covered once. Invalid labels are quarantined;
Golden/Playground remain outside capture. Related launcher/integration siblings
and original task families stay together before windows, with exact/lexical/
normalized-copy checks and frozen splits. Natural and focused scores stay separate.
The neural model retains the existing 512-byte context and independent-pack paths.
