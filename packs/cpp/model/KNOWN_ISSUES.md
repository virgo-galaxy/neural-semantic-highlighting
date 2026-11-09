# C++ known issues

A usable source-display baseline with bounded syntax/local-scope supervision.
Natural test, focus tasks and visible probes are separate evidence in
[BENCHMARKS.md](BENCHMARKS.md); pooled F1 does not promise perfect files.

- Multiline raw strings remain the weakest displayed probe (83.02% exact-span F1).
  The raw literal can split into multiple spans or acquire wrong interior roles.
  Ordinary multiword format/output strings can also split. No runtime parser or
  regex repair is used to conceal these errors.
- Local variables, range-loop/structured-binding names and repeated parameters
  can exchange roles. Class fields may become local variables, especially in
  longer methods. The displayed binding, class and owning-pointer probes retain
  concrete examples.
- Template and dependent names, constructor/type calls, standard-library members,
  concept `requires` and attribute delimiters can be wrong. Source-local Gold does
  not resolve whole-project templates, overloads, ADL, aliases or all class scopes.
- Declaration modifiers are predicted separately and may be wrong with otherwise
  correct colors. Eleven of 29 visible neural Golden cases match all boundaries,
  roles and modifiers exactly; the offline teacher passes all 29 marked cases.
- Ten inspected natural validation files span 78.92%–100% exact-span F1. Conditional
  compilation, macros and external/platform names remain weaker than simple code.
- The fixed grammar quarantined 57 of 207 captured files, including all seven fmt
  files. Accepted natural evaluation therefore uses Catch2, spdlog and LevelDB;
  it does not establish fmt-specific coverage. Raw original files and errors stay
  preserved. Missing forms are not relabeled with a fallback parser.
- Targets common C++11–20 and accepted modern forms; no certification of every
  C++23/26 or compiler extension, modules, coroutine/project environment, ABI or
  embedded language is implied. `.h` filename routing stays C; explicit C++ header
  text uses `cpp`. C and C++ remain separate models.
- The unchanged 512-byte context limits long strings/macros/templates and distant
  relationships. Long documents use multiple predicted windows without Gold cuts.
  Rare labels/attributes and complex operator/conversion forms have sparse evidence.

Browser numerical/output checks demonstrate consistency with the selected native
model, not improved language quality. Inference uses no SDK, compiler, header
lookup, preprocessor, source execution or offline grammar.
