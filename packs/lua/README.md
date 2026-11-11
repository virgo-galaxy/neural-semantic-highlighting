# Lua pack

Common Lua functions, lexical locals, closures, methods/metatables, tables, loops,
coroutines, require-style modules, long strings/comments, 5.4 attributes and 5.5
explicit globals/named varargs. Existing Lua/Neovim/LuaRocks-style code uses the
same source-local model without runtime or dependency resolution.

See [semantics](SEMANTICS.md), [dataset](dataset/README.md), [Golden](fixtures/README.md)
and [training](../../training/lua/README.md). Offline Gold uses pinned
[Tree-sitter Lua](https://github.com/tree-sitter-grammars/tree-sitter-lua), not Lua
execution. No SDK or global language package is installed.
