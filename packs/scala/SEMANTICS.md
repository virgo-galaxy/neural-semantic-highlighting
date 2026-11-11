# Scala source-local semantic contract

One `scala` model handles common accepted Scala 2/3 `.scala`, `.sc` and `.sbt`
syntax. Gold uses pinned tree-sitter-scala 0.26.12 with Tree-sitter 0.25.10,
compiled only in ignored project cache with existing Clang. No Scala SDK, sbt,
compiler, package installation, project execution or dependency resolution runs.
Frontend/native inference needs none of these tools and applies no source repair.

Classes, traits, objects and aliases are types; enums and known entries have enum
roles. Top-level/local definitions are functions; member and extension definitions
are methods. Explicit `new` and calls of known local types are constructors;
unknown imported uppercase calls remain functions without capitalization rules.
Explicit constructor val/var and case-class parameters are properties, other
constructor parameters are parameters. Local vals/vars, destructuring and case /
for bindings use source-local lexical scopes; template vals/vars are properties.
Value/type parameters, defaults, curried parameters, closures, shadowing and imports
are approximated without typechecking, overload resolution or implicit search.

Named argument labels are parameters; member selections are properties and calls
are methods. Package/import/export qualifiers and aliases are namespaces.
Annotations are decorators. Givens use local/template value roles; their methods
and using parameters retain ordinary roles. Scala 3 significant indentation,
extensions, enums, unions/intersections and opaque types use the same weights.
New experimental type-system, macro/plugin, capture or staging semantics are not
certified. Formula-like/infix named calls are syntactic methods. XML tag names
use type roles and attributes use property roles, without embedded-language models.

Plain/triple strings and characters are strings. For interpolated strings, CST
interpolation ranges delimit original string fragments (including the interpolator
prefix and closing quotes) and expression spans. The grammar omits ordinary text
from child tokens; boundaries come from its original node ranges, never rescanning
content or evaluating code. Dollar and brace delimiters are punctuation. Raw/f/
custom interpolators retain syntax-only treatment. Comments remain comments.

End-marker nodes also omit the `end` keyword from their children. Its original
node range supplies that keyword, and the accompanying identifier is a label;
this is a bounded offline CST adapter, without runtime source scanning.

Original source bytes, CRLF/CR and Unicode offsets are preserved. Parser errors,
missing/unmapped tokens, Unicode boundary errors and nonspace coverage gaps fail
closed. Grammar acceptance is not compiler correctness or support for every Scala
release, implicit environment, macro expansion, SBT plugin or package API.
