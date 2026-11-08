# Shell measured limits

These describe the selected coverage epoch 16. No source regex repair or external
command execution hides these failures at runtime.

- **Complex natural scripts are weaker than focused grammar.** Natural test F1 is
  84.20% overall. The single Zsh natural test file scores 71.55%; nested expansion,
  function-heavy code and long lexical regions are not parser-equivalent. Small
  natural sample counts limit conclusions for every profile.
- **Bare arguments and command roles can be confused.** Golden loop argument
  `one` becomes keyword; `--brief` becomes string rather than parameter. Real
  validation contains argument/function/variable substitutions and string range
  errors. The display probe's final `build` call becomes keyword. Core command,
  binding, loop and conditional examples work, but this is approximate source-local
  classification rather than executable resolution.
- **Modifiers have false positives.** Golden `greet` receives `default-library`.
  Zsh `print` receives that modifier even though the offline base lexer does not
  annotate it as recognized. Modifier validity rules remove impossible role/modifier
  combinations, but do not inspect names or correct valid-looking wrong flags.
- **Long strings/comments and deep expansion remain finite-context problems.**
  Context is 512 UTF-8 bytes without persistent shell lexical state. Canonical
  touching-string coalescence joins identical predicted regions; it cannot recover
  a wrong role, repair a whitespace overrun or find an unseen delimiter. Heredocs
  and foreign-language bodies do not get separately composed child semantics.
- **Dialect boundaries are deliberate.** POSIX, Bash, Zsh and Csh are not mutually
  executable. Quoted common variable syntax is aligned offline; Csh-specific
  modifiers, advanced Zsh globbing, rare Bash additions, aliases and environment
  behavior are not complete semantic evaluation. Isolated shared syntax can be
  ambiguous without a dialect/runtime context.

Next work should start from actual product snippets and broader independent
natural code, preserving these frozen families. The first final test has already
been read; do not repeatedly optimize against it while calling it unseen. Keep
all existing source revisions, full checkpoints and formal models.
