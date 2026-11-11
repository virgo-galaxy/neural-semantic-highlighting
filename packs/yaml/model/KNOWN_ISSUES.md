# YAML known issues

- Natural test exact-span F1 is 95.34%
  across 12 files; role macro F1 is
  92.66%. Bounded family holdouts limit
  generalization claims. Natural validation scores 87.15% on 11 different files;
  common configurations do not establish uniform accuracy for long CI bodies or
  every application schema.
- Block scalars remain a material weakness: header comments can merge into bodies, indented # lines can receive comment roles, folded bodies can fragment, and JSON-looking literal content can acquire nested property/keyword roles even within the context. Plain/quoted/block scalar and header boundaries, indentation-sensitive key/value roles, anchors/aliases/tags and multi-document context remain approximate. No alias expansion, schema/application validation, legacy YAML 1.1 type guarantee, template execution, embedded-language parsing or runtime parser/spelling repair is provided.
- Mapping keys, plain values, tags and anchor declaration flags can have incorrect
  roles. Context is 512 original UTF-8 bytes; long/nested content, indentation and
  Unicode can split boundaries. No parser or spelling-based runtime fix hides these errors.
- The independent teacher passes 40 marked cases and 14
  tests; the neural model is entirely exact in 15/40
  Golden cases. Eight displays and ten inspected natural validation files are
  development evidence, separate from the first held-out test. Original-text and
  browser parity checks establish consistency, not semantic perfection.
