# Swift source-local semantic contract

Original `.swift` UTF-8 source, with public UTF-16 half-open spans. Common modern
Swift functions, types, protocols/extensions, enums, generics, local bindings,
closures, patterns, async/actors, attributes/property wrappers, literals, macros
and SwiftUI builder syntax share one entry. Target syntax is accepted by the pinned
official SwiftParser in Swift 6.4.2, not all historical or experimental dialects.

Offline Gold uses official source-accurate parser tokens and trivia. It never
imports/typechecks source, expands macros, resolves packages or executes builds.
Only our parser helper is compiled. Parse errors, missing/unknown tokens,
non-whitespace coverage gaps and invalid original Unicode boundaries fail closed.
Comments and literals preserve original source; plain/raw/multiline/regex literals
are strings. Interpolated expressions keep code roles and punctuation delimiters.

Named structs/classes/actors/protocols/aliases are types, enums are enums. Generic
parameters are type-parameters. Declarations have the declaration modifier;
references do not. Local source scopes approximate parameters, functions, methods,
properties and variables, including shadowing. Both let and var bind variables;
member bindings are properties, without pretending immutable Swift let is const.
Initializers are constructors; deinit is a method. Explicit known local type calls
and `.init` are constructors; unknown imported calls remain callable syntax, with
no capitalization heuristic. Imports are namespaces; argument labels are
parameters; tuple labels are properties. Attributes and macro names are decorators.

SwiftUI uses these same rules: View types, @State/@Binding/@ViewBuilder, trailing
closures and #Preview need no separate model. This does not validate framework
APIs, property-wrapper generated members, result-builder/macro expansion or
platform availability. External names, shorthand enum cases, condition/guard
bindings, generated members and distant symbols remain bounded
source-local approximations. Browser/native inference is entirely neural and
never loads the offline parser, Swift SDK or source-spelling repairs.
