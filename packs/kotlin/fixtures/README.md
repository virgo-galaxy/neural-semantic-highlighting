# Independent Kotlin Golden

32 manually marked cases cover functions/bindings, generics, primary properties,
constructors, enums, lambdas/implicit it, labels, extensions, annotations, suspend,
context parameters, raw/short/long/multi-dollar templates, nested comments,
backtick names, Unicode/CRLF and Kotlin script/Gradle syntax. Their expectations
are authored independently of the teacher; these visible probes never become
corpus collection or training roots.

`make test-labeling-kotlin` also checks shadowing, constructor initializer/member
scope, local declarations, type-only parameters, accessors, BOM/astral positions,
invalid input and parse-only scripts/dependency annotations. No SDK or project
execution is needed. `make challenge-kotlin KOTLIN_CHECKPOINT=...` compares neural
predictions with these same expectations, retaining missing/unexpected spans.
Visible Golden/display accuracy is distinct from natural held-out test evidence.
