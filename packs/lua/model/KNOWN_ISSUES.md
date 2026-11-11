# Lua known issues

- Natural test exact-span F1 is 91.78%
  across 15 files; role macro F1 is
  89.22%. Bounded family holdouts limit
  generalization claims. Grammar acceptance is not full compiler or API validity.
- Long/delimited string and comment boundaries, table/method roles, closure captures, dynamic metatables and distant lexical bindings remain approximate. No Lua/Neovim/LuaRocks execution, dependency resolution or full LuaJIT/Luau dialect compatibility is claimed.
- Names, declaration flags, imported calls and distant scopes can have incorrect
  roles. Context is 512 original UTF-8 bytes; long/nested content and Unicode names
  can split boundaries. No parser or spelling-based runtime fix hides these errors.
- The independent teacher passes 32 marked cases and 13
  tests; the neural model is entirely exact in 10/32
  Golden cases. Eight displays and ten inspected natural validation files are
  development evidence, separate from the first held-out test. Original-text and
  browser parity checks establish consistency, not semantic perfection.
