# C# measured limits

- **Complex property patterns are weaker.** The Records display probe can assign
  string roles to `: >= 100`, `Name: var` or a closing brace, and confuse discard,
  pattern variable and parameter roles. Record names/components can become method,
  constructor or parameter. The raw display/Golden reports retain these failures.
- **Local names and qualifiers remain approximate.** Individual fields/properties
  become parameters, enum names can become class and constants become properties.
  Distant parameters/queries are less reliable in long Dapper source. Unknown
  external type qualifiers, extension methods, anonymous objects and cross-file
  semantics are not resolved through a compiler or project environment.
- **String boundaries remain bounded.** The reviewed Hello, async-stream and complex
  raw/interpolated StringTemplates probes improved in the mixed revision. This does
  not certify arbitrary quote nesting or long comments/literals beyond 512-byte
  context. Formatted-string bodies stay opaque strings, not embedded expression,
  JSON/SQL/HTML or Razor language composition. No grammar repairs neural output.
- **Golden flags are strict.** Small probes retain local declaration-flag, name-role
  and boundary differences, even where display colors coincide. Read the raw Golden
  report; successful parser labeling is not a claim of exact neural predictions.
- **Offline grammar scope is explicit.** Tree-sitter C# 0.23.5 has ambiguities and
  incomplete cases, including captured list slices/guarded list patterns. Eight
  original source files were quarantined. Supported basic list patterns are trained;
  not every modern/preview feature is certified. No .NET SDK or Roslyn validation
  took place. C# script `#r`/`#load`, `.csx` certification, Razor, XAML, `.csproj`,
  `.sln`, source generators, project builds and assembly/bytecode are separate scopes.
- **Evidence is bounded.** Natural test uses small source-family holdouts from three
  pinned upstreams; focused modern syntax is separate evidence. Test inspection
  occurred only after candidate review/freeze and did not trigger further training.
  Those archived test files are known for future comparisons; preserve all history.
