# Rust known issues

A usable bounded source-display baseline, not a project analyzer.

- Raw, byte/C raw strings, nested/long literal content and named format strings
  can split or exchange roles with punctuation/identifiers. The mixed raw-string
  display probe scores 74.07% exact-span F1 even after a bounded literal revision.
  Identically colored adjacent pieces still count as boundary errors. No runtime
  lexer, delimiter scanner or source-spelling repair hides them.
- Natural test F1 is 94.90% over
  15 files; role macro F1 is
  79.62%. Local field/parameter/variable,
  type/trait/namespace, enum-variant, lifetime and constant roles can be confused.
  Declaration flags may be wrong even when visible colors are acceptable.
- Macro bodies are CST token trees, with lexical inner roles and no expansion.
  User-defined DSLs, generated items, procedural macros, derives and external crate
  semantics are not resolved. Only recognized hidden repetition separators are
  recovered offline; unsupported separators are quarantined.
- Destructuring/guard bindings, closures/captures/shadowing, associated types,
  const generics and qualified calls remain approximate. Import names are namespace
  roles, without fabricated dependency/type resolution. Unknown method calls are
  callable syntax, not certified method dispatch.
- The neural model is completely exact in 7/23 visible Golden
  cases; the separate offline teacher passes all 23. Display source
  and ten inspected natural validation files are development diagnostics.
- Common syntax accepted by Rust grammar 0.24.2 is the target. Every stable 1.99
  feature, nightly extensions and edition compatibility are not certified by
  highlighting. C strings require 2021 or later in compiler probes. The unchanged
  512-byte context limits distant bindings, long literals/comments and macro bodies.
- Source preservation and browser/native parity verify unchanged text/consistent
  predictions; they do not establish perfect role accuracy or compiler semantics.

The existing stable Rust toolchain was explicitly updated at the user's request.
No Cargo packages/nightly/compiler SDK beyond that update were installed. Collected
source never builds/runs, expands macros or follows modules/dependencies. Inference
requires no Rust, Python, Cargo or parser. Earlier data, experiments and every
previous native/browser model remain preserved.
