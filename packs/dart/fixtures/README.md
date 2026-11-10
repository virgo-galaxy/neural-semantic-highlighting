# Dart Golden

35 independently hand-marked original UTF-16 cases cover functions, bindings,
fields/constructors/getters, generics/enums, calls/arguments, imports, records and
patterns, catches/async, annotations, plain/raw/multiline/interpolated strings,
Unicode/BOM/CRLF, labels, modern primary constructors, extension types, wildcards,
dot shorthands and symbols.

Expectations are authored separately from the CST teacher. Golden and Playground
never enter training capture. Syntax uses the pinned independent grammar; no
SDK/compiler validity or full-project semantics are claimed.

The separate `flutter-golden.json` adds eight hand-marked framework probes for
build methods, named widget arguments, state/callbacks, async builders, disposal
and initializing `super.key`. They retain the canonical Dart semantic contract
and are excluded from training. The original 35-case Dart suite is unchanged.
