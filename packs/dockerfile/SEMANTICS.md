# Dockerfile semantic contract

This pack highlights original Dockerfile/Containerfile source, not a built image.
`dockerfile`, `docker` and `containerfile` select one model. Filename examples
include `Dockerfile`, `Dockerfile.production` and `build.dockerfile`; the consumer
passes an explicit language. No content-based language detection occurs.

All spans use original UTF-16 `[start,end)` positions, preserve UTF-8 source,
BOM/CRLF, comments, case, quotes, blank lines and Unicode, and never overlap.
Non-whitespace source must be covered. Whitespace may stay outside spans except
inside strings/comments/opaque bodies. No instruction, shell command, copied
file, image reference or dependency is executed, resolved or downloaded by Gold.

## Roles

- Instruction words are `keyword`, preserving original case. `AS`, the nested
  instruction in `ONBUILD`, and `CMD`/`NONE` in `HEALTHCHECK` are also keywords.
- Recognized top parser directives keep `#` as punctuation, the directive name
  as keyword, `=` as operator and the value as string. Other Docker comments
  are comment spans. An inline hash outside a RUN shell remains literal data.
- Leading instruction flags are `parameter` spans, including their `=value`.
  Docker line-continuation escape characters are punctuation; comments removed
  from logical continuations retain their own original comment ranges.
- FROM image/stage-base literals are `namespace`; unquoted dollar references
  are variable. The name after AS is `label+declaration`. No image or stage-name
  resolution is claimed; COPY --from values remain part of parameter spans.
- ARG/ENV names are `variable+declaration`; LABEL keys are
  `property+declaration`. Assignment equals signs are operators. Quoted values
  remain whole strings, including their quote characters; unquoted references
  are variable spans. Numeric-looking ordinary literals use number; this is a
  source display role, not Docker environment-value type inference. Legacy
  space-separated ENV/LABEL values remain one original literal region.
- Other plain arguments/paths are strings, with unquoted dollar references
  separated as variables. JSON forms reuse existing JSON string, keyword,
  number, property and punctuation supervision without interpreting strings.
- Common default POSIX/Bash shell forms reuse the existing offline Shell
  teacher's keyword/comment/string/number/operator/punctuation/function/
  variable/parameter roles, declaration and default-library modifiers. An
  explicitly declared known sh/bash/zsh/csh SHELL changes that offline profile;
  other explicit/custom shells stay opaque strings. FROM resets that state.
  The neural model approximates source-local roles within its bounded context.
- Heredoc operators are operator, opening quoted/unquoted delimiters are
  `label+declaration`, closing delimiters are label. Their original body and
  terminator positions/order must match BuildKit. RUN-only heredocs (optionally
  naming sh/bash/ash) reuse Shell body supervision, including blank lines.
  COPY/ADD file bodies, redirected stdin and shebang/custom-interpreter bodies
  stay opaque strings. No language is guessed from their contents. Tab stripping
  affects parser matching only; output coordinates/text retain original tabs.

Only variable/property/label/function may carry declaration, and only function may
carry default-library. These validity rules are shared by Gold and neural decoding;
no source-dependent repair, regex/parser fallback or source spelling runs at
inference. The runtime does not load BuildKit, Go, Shell tooling or a JSON parser.

## Offline evidence and limits

The independent structural oracle is official BuildKit v0.35.0's parse-only AST,
compiled by the already installed Go SDK with automatic SDK download disabled.
The helper, module checksums, Go dependency lock, binary/compiler hashes and
licenses are retained in the isolated project tool cache. Source-local spans are
mapped through checked logical-header/original-character maps; no formatted
source substitutes for the input. Existing pinned Shell and JSON assets supply
only offline nested supervision. Unknown instructions, invalid heredocs,
unsupported controls, AST/source mismatches and uncovered source are quarantined.
AST acceptance is not complete Docker build validation, image/platform support,
variable expansion or successful container execution. Long bodies, distant stage
context, custom shells and unusual interpreter combinations remain measured
limitations. Independent marked Golden and visible probes never enter training
collection roots; actual natural validation and first held-out test are separate.
