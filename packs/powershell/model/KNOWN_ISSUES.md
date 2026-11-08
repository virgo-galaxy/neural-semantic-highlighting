# PowerShell measured limits

- **String ranges can split.** The function display probe splits a quoted
  greeting around its comma; the two-Here-String probe splits the second opening
  marker from its body while retaining string roles throughout the body/end.
  Short standalone Here-String Golden probes have more boundary/role errors.
  Opaque whole-string Gold does not mean every neural range is exact.
- **Long bodies can lose state.** One natural validation security module reaches
  only about 54% non-whitespace character-role agreement, with long embedded
  quoted/comment content. This development diagnostic is not corpus exact-span
  F1 or rendered-color accuracy. Context remains 512 UTF-8 bytes; there is no
  interpreter fallback or source-regex repair.
- **Name roles and flags are approximate.** Pipeline argument names such as
  Length can become function/property instead of string-like bare arguments.
  Class members, static method/type boundaries, automatic variables and
  declaration/default-library modifiers also have errors. Offline Gold uses
  visible lexical roles, not module lookup, type inference or full scope analysis.
- **Scope is source display.** Common Windows PowerShell and modern PowerShell
  spellings share one entry. Full DSC/workflow, module-specific semantics,
  complex interpolation and every host/version are not certified. Strings,
  including Here-String interpolation, stay opaque rather than composing an
  embedded language. `.psd1` support is PowerShell source, not general file formats.
- **Evidence is bounded.** The first natural test has only three retained files
  from one official upstream capture. Focus tasks and Golden are separate from
  natural evidence. Read BENCHMARKS.md and raw reports; preserve the known first
  test and every original dataset/checkpoint for future comparisons.
