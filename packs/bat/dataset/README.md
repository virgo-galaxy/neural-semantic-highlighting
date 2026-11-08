# BAT / CMD corpus

A bounded capture pins eleven official VS Code batch scripts and the complete
original MIT license. Exact Git blobs and SHA-256 locks retain original source.
Related code launchers share a family, as do integration-test variants; no scripts
are executed, followed or used to install an environment.

Original task families cover percent/delayed/argument/loop variables, labels,
CALL/GOTO, IF/FOR, quoting, redirection, pipes, command chains and caret spelling.
Related positions, casing, `.bat`/`.cmd` names and CRLF stay in the same task family.
Golden and Playground are excluded from collection. Keep all immutable revisions.

The bounded offline adapter also confines FOR /F quoted-command matching to one
physical line, preventing the upstream rule from backtracking through later
commands. The original full VS Code regression script stays unchanged.
