# JSON / JSONC known issues

- Natural test exact-span F1 is 99.78%
  across 15 files; role macro F1 is
  99.82%. Bounded family holdouts limit
  generalization claims. Grammar acceptance does not establish schema or application
  configuration validity. JSONC natural validation scores 92.90% on five files,
  compared with 99.84% on six test files; these small, different family holdouts
  do not establish uniform performance across all configurations.
- Very short empty-container/primitive and comment-plus-container snippets can merge spans or misclassify keywords. Quoted-key/value roles, escapes and long string/comment boundaries across the 512-byte context remain approximate. No schema/type validation, JSON5 syntax, embedded-string parsing, automatic format detection or runtime parser/spelling repair is provided. JSONC explicitly accepts trailing commas; strict JSON supervision rejects them and comments, while runtime highlighting itself is not a syntax validator.
- Property names and string values can receive incorrect roles; the reused model
  schema can also produce roles/modifiers unused by the JSON contract. Context is
  512 original UTF-8 bytes; long/nested content, escapes and Unicode can split
  boundaries. No parser or spelling-based runtime fix hides these errors.
- The independent teacher passes 48 marked cases and 13
  tests; the neural model is entirely exact in 35/48
  Golden cases. Sixteen displays and ten inspected natural validation files are
  development evidence, separate from the first held-out test. Original-text and
  browser parity checks establish consistency, not semantic perfection.
