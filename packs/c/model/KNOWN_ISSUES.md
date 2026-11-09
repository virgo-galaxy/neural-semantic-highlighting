# C known issues

This is a usable display baseline with source-local grammar supervision. Natural
independent test, focus tasks and visible probes are separate evidence in
[BENCHMARKS.md](BENCHMARKS.md); pooled F1 does not promise perfect files.

- Multiword/Unicode strings and include paths can split into adjacent spans of the
  same color. `hello.c` still splits its format string; `literals.c` can split a
  hexadecimal floating literal. No runtime source repair is used to hide this.
- Callback callees may become `function` instead of `parameter`; repeated pointer
  parameters, typedef names and local variables can exchange roles. The displayed
  callback/linked-list/modern-C probes retain examples of these errors.
- Macro replacement arguments, `__VA_ARGS__`, external constants and header names
  are weaker. `macros.h` retains errors around the include path and log arguments.
  Preprocessor branches are displayed, not evaluated or expanded.
- Declaration modifiers are independent predictions and can be wrong even when
  the visible token color is correct. Eleven of eighteen visible neural Golden
  cases match all roles, boundaries and modifiers exactly; teacher Golden is 18/18.
- Ten natural validation files span 86.53%–100% exact-span F1. Platform-specific
  preprocessor configurations remain weaker than straightforward headers/functions.
- This pack treats `.h` explicitly as C. It does not detect C++ headers or support
  C++, Objective-C, assembly bodies, every C23/GNU/compiler extension or external
  project type resolution. Thirty-eight captured files outside the pinned grammar
  were quarantined; their source and errors remain preserved.
- The 512-byte context bounds long comments, literals, macro bodies and distant
  declarations. Long documents use multiple predicted windows without Gold cuts.

Browser conversion/parity checks establish consistency with the selected native
model; they do not remove these neural/teacher limits. There is no compiler, SDK,
header lookup, parser or source execution in inference.
