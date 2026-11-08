# AWK measured limits

- **Regex boundaries can split.** Bare alternation and short substitution regex
  Golden cases can fragment even when the fragments keep regex coloring. The
  GNU display example's `/ready|complete/` has this measured boundary error.
  Regex-vs-division remains approximate, especially near unusual surrounding code.
- **Advanced GNU calls have role errors.** Indirect `@fn(...)` and coprocess
  variable names can be merged or mislabeled. GNU phase/builtin-variable modifier
  flags and custom function calls also have occasional false flags. Direct fields,
  ordinary functions, arrays and loops are stronger in the displayed examples.
- **Context and resolution are bounded.** Context is 512 UTF-8 bytes; long
  comments/strings or distant declarations can lose state. This is source-local
  display, not variable-scope analysis, dynamic function resolution or execution
  compatibility with every AWK implementation. Includes/extensions are never run.
- **Evidence is small.** Natural test has six source-family-held-out files from
  GNU examples/libraries; its 96.89% F1 does not imply universal POSIX/GNU coverage.
  Focus test F1 is 99.87% and remains separate from natural evidence. The archived
  first test is already known; preserve it and all historical checkpoints/data.
