# Kotlin known issues

- Natural test exact-span F1 is 94.57%
  across 31 files; role macro F1 is
  76.86%. Small family holdouts and four
  projects do not establish universal Kotlin/JVM/Android/Gradle compatibility.
- The mixed string display scores 76.51%.
  Plain/raw/multi-line/multi-dollar template delimiters and interpolated names can
  split or change roles. Long content crossing the 512-byte context, nested
  comments and escaped backtick names can also have incorrect boundaries.
- Constructor/function/method, enum/type/type-parameter, parameter/property/variable
  and declaration flags remain approximate. Gold is source-local and imported
  uppercase calls stay syntactic functions; no capitalization heuristic or
  dependency/type resolution is used. Distant declarations and implicit lambda
  receivers/`it` cannot always be resolved with this context.
- Context parameters, newer syntax, callable references, delegated properties,
  labels and annotation use-site targets have bounded training coverage.
  Kotlin code, scripts, Compose and Gradle syntax share weights; no plugin,
  framework API, build-file execution or full project compatibility is certified.
- The teacher passes 32 marked cases and 13 tests; the neural model is exact in
  16/32 Golden cases. Eight displays and ten inspected natural
  validation sources are visible development evidence. The first test remains
  separate. Browser parity and unchanged source text measure consistency, not accuracy.
