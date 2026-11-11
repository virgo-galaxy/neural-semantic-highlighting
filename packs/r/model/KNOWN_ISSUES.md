# R known issues

- Natural test exact-span F1 is 96.04%
  across 15 files; role macro F1 is
  95.87%. Bounded family holdouts limit
  generalization claims. Grammar acceptance is not full compiler or API validity.
- Long raw/delimited strings, backtick names, comments, closure and dynamic-call roles remain approximate. Formula names, tidy evaluation/NSE, environments/promises and S3/S4 dispatch are source-local approximations, without R package/type resolution.
- Names, declaration flags, imported calls and distant scopes can have incorrect
  roles. Context is 512 original UTF-8 bytes; long/nested content and Unicode names
  can split boundaries. No parser or spelling-based runtime fix hides these errors.
- The independent teacher passes 32 marked cases and 10
  tests; the neural model is entirely exact in 13/32
  Golden cases. Eight displays and ten inspected natural validation files are
  development evidence, separate from the first held-out test. Original-text and
  browser parity checks establish consistency, not semantic perfection.
