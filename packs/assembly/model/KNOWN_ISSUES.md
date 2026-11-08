# Assembly measured limits

- **Macros remain weaker.** The NASM display probe labels macro declarations and
  `%1`/`%2` operands incorrectly in a few places. The short AArch64 macro Golden
  mislabels its header and merges `#\amount` into a string-like region. These are
  neural prediction errors; no macro expansion or assembler repair is used.
- **Names and metadata have role errors.** Individual branch labels, EQU/data
  symbols, `.type`/`.size` references, `noprefix`, `casemap` and `default rel`
  receive wrong function/variable/keyword/operator roles. MASM ENDP references
  can carry an extra declaration flag. The common NASM/AT&T/MASM display probes
  remain readable but are not completely exact.
- **Vector flags are incomplete.** The AArch64 vector Golden correctly labels
  `v0.4s`/`v1.4s`/`v2.4s` as variables but misses default-library modifiers.
  Exotic register forms/ISA extensions and non-x86/AArch64 architectures are not
  certified. Gold itself supplies bounded source-local roles, not ISA validation.
- **Comments/strings can lose boundaries.** A multiline block-comment Golden
  temporarily labels an interior word as keyword. A short Unicode/CRLF data Golden
  splits a quoted string and swaps the binding/directive roles, despite preserving
  original UTF-16 positions. Long comments/strings and distant labels remain limited
  by 512-byte context. Touching predicted comments coalesce without source repair.
- **Dialect scope is explicit.** Semicolon-separated GNU instructions, MASM COMMENT
  blocks, arbitrary macro dialects, full preprocessor branches, linker resolution
  and every assembler/version are outside this initial baseline's guarantees.
  Assembly `.inc` coverage does not claim all files with that extension.
- **Evidence is small.** Natural test contains five source-family-held-out files:
  two NASM and one each GNU/AT&T, MASM and AArch64, from three upstream projects.
  Profile/focus/Golden/display scores stay separate. They are source-display
  evidence, not architecture execution tests or universal assembly accuracy.
  The archived first test is known for future comparisons; preserve all history.
