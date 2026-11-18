# Makefile known issues

- Independent natural exact-span F1 is **89.14% on 17 files**;
  validation is **86.94% on 11 other files**. Authored focus is
  98.59%; eight visible probes 95.54%.
  Small bounded cohorts do not establish uniform accuracy for every project.
- Strict neural Golden is **29/46** whole cases exact including modifiers.
  Nested/substitution variable boundaries, directives versus bindings, literal
  prefix values, declaration modifiers and recipe flags can still be confused.
- Long shell commands/quoted strings, continued comments, define bodies and
  distant target/variable/prefix state remain weaker under 512-byte context.
  Source is always preserved even when a span role or boundary is wrong.
- The offline grammar is bounded GNU Make supervision, not a full GNU Make
  evaluator. Some newer `:::=`, static patterns with order-only prerequisites,
  computed names/nested defines and unusual recipe/here-document combinations
  can be outside the oracle. Unsupported originals remain quarantined.
- Only literal unconditional one-character recipe prefixes/reset are supervised;
  computed/conditional prefixes are rejected offline. Foreign/computed SHELL
  conservatively makes recipe/explicit shell bodies opaque for that document.
  Complete BSD make, NMake, CMake, Automake input and arbitrary Windows shells
  are not claimed. No variable expansion, included-file loading, execution,
  dependency resolution or runtime parser/regex/spelling repair occurs.
- Browser parity and Markdown reuse establish consistent original span/text
  behavior, not perfect composed semantic accuracy. Canonical touching-string
  union never bridges a whitespace gap or repairs a wrong role.
