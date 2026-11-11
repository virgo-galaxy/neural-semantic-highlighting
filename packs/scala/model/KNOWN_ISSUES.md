# Scala known issues

- Natural test exact-span F1 is 89.00%
  across 30 files; role macro F1 is
  76.05%. Bounded family holdouts limit
  generalization claims. Grammar acceptance is not full compiler or API validity.
- Long plain/raw/interpolated strings, generic/type and enum/constructor roles, implicit receivers and distant symbols remain approximate. Given/using and extension syntax is source-local, without implicit search, overload resolution, macro/plugin execution, framework APIs or experimental type-system certification.
- Names, declaration flags, imported calls and distant scopes can have incorrect
  roles. Context is 512 original UTF-8 bytes; long/nested content and Unicode names
  can split boundaries. No parser or spelling-based runtime fix hides these errors.
- The independent teacher passes 33 marked cases and 13
  tests; the neural model is entirely exact in 17/33
  Golden cases. Eight displays and ten inspected natural validation files are
  development evidence, separate from the first held-out test. Original-text and
  browser parity checks establish consistency, not semantic perfection.

The independent Kyo effect-heavy Scala 3 holdout is materially harder than
ordinary displays. Higher-kinded/effect/contextual types, macros and deep scopes
have bounded coverage; see the per-source breakdown in BENCHMARKS.md.
