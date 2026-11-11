# Ruby known issues

- Natural test exact-span F1 is 86.96%
  across 15 files; role macro F1 is
  81.02%. Bounded family holdouts limit
  generalization claims. Grammar acceptance is not full compiler or API validity.
- Heredoc/percent/regex/interpolated string boundaries, destructuring/pattern bindings, constant/type and top-level/member call roles remain approximate. Dynamic dispatch, metaprogramming, Rails/Rake DSLs, generated classes, refinements and distant scopes are source-local approximations without Ruby/gem execution or dependency resolution.
- Names, declaration flags, imported calls and distant scopes can have incorrect
  roles. Context is 512 original UTF-8 bytes; long/nested content and Unicode names
  can split boundaries. No parser or spelling-based runtime fix hides these errors.
- The independent teacher passes 33 marked cases and 13
  tests; the neural model is entirely exact in 10/33
  Golden cases. Eight displays and ten inspected natural validation files are
  development evidence, separate from the first held-out test. Original-text and
  browser parity checks establish consistency, not semantic perfection.
