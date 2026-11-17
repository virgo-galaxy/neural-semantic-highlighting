# Dockerfile known issues

- First independent natural exact-span F1 is **96.33%**
  on 14 files; role macro F1 is 95.62%. The 12-file
  validation score is lower (88.00%); these
  bounded family cohorts do not certify every project, feature or platform.
- Real test strings reach 94.88%, image/base
  namespaces 93.75%, and properties
  92.31% (only 6 reference keys). Literal
  paths/image/stage names, shell option/value boundaries, quotes and flags can
  still be confused. Declaration/default-library modifiers are approximate.
- Strict neural Golden remains **23/42** whole cases exact including modifiers,
  with 85.41% base-span F1. BOM/Unicode
  comments may receive string roles; function/flag/delimiter boundaries can be
  wrong. The Unicode display is 95.00%, despite its opaque heredoc body being exact.
- Two visible English/Unicode heredoc bodies are complete, but 512-byte context
  still limits long bodies, distant stage/binding context and uncommon shell
  constructs. Canonical touching-string union does not bridge gaps or repair a
  wrong role. All source text remains preserved even when a role is missed.
- Common POSIX/Bash forms use source-local learned roles. Explicit foreign/custom
  shells, shebang-language heredocs and COPY/ADD inline files stay opaque in
  their documented cases. No source-content language guessing, full Windows-shell
  guarantee, variable expansion, image/platform validation, container execution,
  dependency resolution or runtime parser/regex/spelling repair is provided.
- JSON and Shell supervision is offline; runtime uses one standalone model.
  Markdown reuse depends on its predicted body/info region and registered models;
  complete composed semantic accuracy is not established by base Dockerfile F1.
