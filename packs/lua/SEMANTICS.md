# Lua source-local semantic contract

Original `.lua` source uses one `lua` model. Pinned Tree-sitter Lua 0.5.0 and
Tree-sitter runtime 0.25.10 provide offline CST supervision, compiled only with
existing Clang in ignored project cache. No Lua SDK, interpreter, LuaRocks or
Neovim runtime is installed, and collected code never executes. Frontend inference
uses neural weights without a parser, interpreter or source-spelling repair.

Local declarations bind after their initializer, including closures; `local function`
binds recursively before its body. Functions, blocks and loops have lexical scopes.
Loop bounds see outer bindings, and repeat-body locals remain visible in `until`.
Parameters and callback invocations keep parameter roles. Colon methods bind implicit
`self` inside their body. Direct call names are functions; dot/colon calls are methods.
Bare table keys and extracted fields are properties; computed keys keep expression
roles. Function-valued bindings/fields use function/method declarations. No name-based
capitalization, API inventory or type heuristics are used.

Lua 5.4 `const` and `close` attributes, Lua 5.5 global declarations and named varargs
are covered by the pinned grammar. Explicit const bindings are constants; attributes,
`global none` and ordinary syntax words are keywords. Contextual `global`/`none`
remain ordinary identifiers elsewhere. Varargs are parameters, labels and goto
names are labels. Whole plain/long strings (including equal-sign delimiters) and
comments retain original ranges; pattern strings and embedded-looking text remain
strings rather than executed or interpolated source.

UTF-8 parser bytes map to original UTF-16 offsets without normalizing Unicode or
CRLF. Error/missing nodes, NUL, unknown tokens, overlap and nonspace coverage gaps
fail closed. Grammar acceptance is not compiler validation or complete release
compatibility. Dynamic metatables, require/import resolution, globals, distant
scopes, LuaJIT/Neovim APIs and other embedded dialects remain local approximations.
Luau is a separate language and is not advertised as a Lua alias.
