# Kotlin source-local semantic contract

Original `.kt` and `.kts` source shares one public `kotlin` document kind. Offline
profiles distinguish ordinary Kotlin from scripts; they are not separate models.
Common modern classes/interfaces/data/value/sealed types, functions/extensions,
properties, generics, nullable/pattern expressions, lambdas, suspend/coroutine code,
annotations, delegated properties, string templates and Compose syntax are covered.
Accepted syntax is bounded by the pinned official Kotlin 2.4.21 parser, not every
historic, experimental, compiler/plugin or SDK combination.

Gold uses official parse-only PSI and lexer components in isolated project cache,
run by the existing JDK 22. No Kotlin SDK, Gradle, Android SDK or global dependency
is installed. PSI requires normalized parser newlines: a reversible UTF-16 offset
map restores original CRLF/CR and BOM positions. Original source bytes are never
changed in collection, training or rendering. Parse errors, unknown tokens,
overlap, Unicode boundary errors and non-whitespace coverage gaps fail closed.

No imported code, script, annotation, dependency resolver, compiler plugin or
project build executes. Scripts are parsed as scripts, never evaluated. This is
source-local supervision, without typechecking or symbol/project resolution.

Classes/interfaces/objects/aliases are types, enums and entries have enum roles;
known local type calls and explicit constructor callees are constructors. Unknown
imported calls remain syntactic functions without capitalization heuristics.
Member functions/calls are methods, top-level and extension declarations are
functions. Local `val`/`var` bindings are variables; class/object properties and
primary constructor `val`/`var` parameters are properties; `const val` is constant.
Value/type parameters, destructuring, local shadowing and implicit lambda `it`
are approximated with lexical scopes. Implicit backing `field` and setter `value`
are scoped to accessors. Non-property constructor parameters are available to
initializers but masked in ordinary member methods/accessors.

Package/import paths and aliases are namespaces. Named argument labels are
parameters. Attributes/use-site annotations are decorators with keyword targets.
KDoc and nested comments remain comments. Character/plain/raw strings are strings;
short/long and multi-dollar templates retain code expression roles and delimiter
punctuation. Compound operations follow original lexer pieces; only touching
string pieces coalesce in Gold. Declarations have a separate declaration modifier.

Compose annotations, named arguments, state delegation and receiver-style DSLs
use the same Kotlin model. Coroutines, Gradle scripts and UI/framework APIs are
not resolved or executed. Generated members, imported/nested types, receiver-lambda
arity, smart casts, distant scopes and complex callable references remain bounded
approximations. Frontend/native inference stays entirely neural and needs no
parser, JVM, language SDK, compiler or spelling-based prediction repair.
