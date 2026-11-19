# Shell measured limits

These describe the selected short-Here-Document epoch 20. No runtime parser,
source-regex repair or external command execution hides these errors.

- **Here Document endings remain approximate.** New focused holdout F1 is 96.76%,
  but short standalone `<<END`, `<<"DATA"` and `<<-END` Golden cases can absorb the
  following `echo ready` into the string. A post-delimiter redirect case overruns
  its body newline. The actual combined Playground example correctly separates
  all three bodies and subsequent commands, with two extra newlines in one span.
  The literal-body Golden case containing variables/substitutions is exact.
  Finite-context predictions do not guarantee arbitrary delimiter matching.
- **Bodies are opaque strings.** Quoted and unquoted Here Documents do not compose
  embedded SQL/HTML/JS or execute/interrogate expansion. The offline teacher uses
  exact terminator lines, quote removal and tab stripping; inference uses only
  neural predictions. Long bodies beyond the 512-byte context can lose state.
- **Names, arguments and modifiers remain approximate.** `function name()` and
  `function name` syntax is represented, but declaration/default-library flags
  can be missed or spuriously added. Golden bare arguments can become keywords;
  the display example's final `build` call still becomes keyword. Numeric
  parameter defaults and string boundaries around whitespace also produce errors.
- **Complex dialect syntax is weaker.** Known natural F1 is 84.78% overall and
  73.76% on the one Zsh test file. Deep expansion, advanced globbing, Csh modifiers,
  environment/alias resolution and mutually incompatible dialect semantics are
  not complete interpretation. Bash is the priority; other profiles are broader
  approximate coverage through the same model.
- **Evidence is bounded.** The old corpus test has already been read. New Here
  Document tasks are focused authored programs, not new independent projects.
  Keep natural/focus/profile counts separate and do not call subsequent runs on
  either test newly unseen. Preserve all datasets, experiments and formal models.
