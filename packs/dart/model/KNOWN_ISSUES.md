# Dart known issues

A usable bounded source-display model with independent CST supervision.

- Natural test exact-span F1 is 94.22%
  over 20 files; role macro F1 is
  82.21%. Captured official packages
  and Flutter modules form a small holdout, not universal application evidence.
- Raw/regex strings, long/triple literals, interpolation text boundaries,
  embedded expressions and adjacent escapes can split or exchange roles.
  Mixed displayed strings score 85.34%, with full diagnostics retained.
  No runtime string scanner or regex repair masks prediction errors.
- Constructors versus functions/methods, local parameters/properties/variables,
  enum/type/generic roles, nested pattern captures, closures and declaration flags
  remain approximate. Explicit construction and known local classes provide
  stronger constructor evidence; unknown imported widget calls remain syntactic
  functions without a fabricated capitalization or package-resolution heuristic.
- Named argument labels are parameters, not resolved widget properties.
  Flutter uses this same Dart model: no widget API/type validation, generated
  member resolution, build_runner execution or full-project analysis occurs.
- The pinned independent grammar is not Dart's official analyzer. Bounded modern
  forms parse, but every SDK release/feature, legacy language mode, experimental
  syntax and SDK compatibility are not certified. No SDK was installed or used,
  and authored displayed examples have parse/coverage evidence only.
- The separate teacher passes 35 independent cases and eleven tests;
  neural output is fully exact in 6/35. Visible display/Golden
  and inspected validation are development diagnostics, not unseen test scores.
- The unchanged 512-byte context limits distant symbols and long strings/comments.
  Browser/native parity and original source preservation establish consistency,
  not semantic perfection.

Offline labeling never executes source, annotations, imports, generators or
project scripts. Frontends require no Dart, Flutter, Python process or parser.
Previous source snapshots, full training runs and all earlier selected models
remain preserved. Further changes can use these measured limits as known evidence.

[Flutter coverage](FLUTTER.md) adds application/display evidence with these same
weights. Flutter is a public alias and Playground entry, with the canonical Dart
schema and limits; imported widgets are not resolved by a framework analyzer.
