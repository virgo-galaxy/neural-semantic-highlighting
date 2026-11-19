# Java measured limits

- **Local name roles remain imperfect.** Fields/record components can be classified
  as parameters or variables, including compact constructor parameters and distant
  member references. Enum declaration names can become class, and static qualifiers
  can become ordinary variables. The annotation/enum display probe contains these
  errors; its constants improved in the mixed revision but are not universally exact.
- **Guarded switch and patterns have role errors.** A deconstruction type can become
  constructor, a pattern binding can become parameter, and `when`/`default` can receive
  an ordinary-name/string role. The separately authored routing example measures these
  failures. Parsing and full pattern-flow scope are not reconstructed at runtime.
- **String boundaries can fragment.** Quotes around short whitespace-containing
  strings, formatted-string bodies and long comments/text blocks can split into
  several predicted spans. The reviewed HTML text-block display probe is exact, but
  this does not certify arbitrary embedded content or literals beyond 512-byte context.
  Embedded HTML/SQL/JSON in Java strings remains string content, not composed languages.
- **Module paths are a bounded baseline.** Module words are covered, but individual
  service/implementation/package path components can swap `namespace`/`type` roles.
  The reviewed module descriptor scores below ordinary class/interface examples.
- **Golden flags are stricter than display.** Small independent probes retain local
  role, Unicode/string-boundary and declaration-flag differences. The raw Golden and
  real-source reports are committed; they are not silently repaired or omitted.
- **Scope and evidence are explicit.** Gold uses JDK 22.0.1 parse-only syntax, without
  project classpaths, overload resolution or annotation execution. Source-local scope
  does not fully implement cross-file or pattern-flow semantics. Preview and later
  syntax, bytecode/JAR input, JShell transcripts, JSP and every Java framework/version
  are outside this initial certification. Training targets ordinary source display.
- **Natural holdouts are small.** The pinned library/JDK capture is a bounded sample;
  its first natural test and focused modern tasks must remain separate. Test inspection
  happened after freezing the candidate and did not trigger further tuning. Those
  archived files are known for future comparisons; preserve all prior experiments.
