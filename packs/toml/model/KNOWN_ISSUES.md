# TOML known issues

- Natural test exact-span F1 is 99.10%
  across 9 files; role macro F1 is
  97.52%. Bounded family holdouts limit
  generalization claims. Parser acceptance is not project/schema validity.
- Multiline string bodies remain a material weakness: original quoted/hash/shell-looking content can fragment or receive comment/property roles even inside the 512-byte context (strings.toml display 68.42% F1). Quoted keys containing dots can split or acquire the header role (keys.toml 91.89%). Header/assignment roles, dates and long bodies remain approximate. Common 1.0 and tested 1.1 forms do not certify every TOML edge case; the pinned parser labels 1.1 support experimental. No project validation, configuration execution, interpolation or runtime parser/spelling repair is provided.
- Header/assignment keys, dates and string boundaries can have incorrect
  roles. Context is 512 original UTF-8 bytes; long/nested content and
  Unicode can split boundaries. No parser or spelling-based runtime fix hides these errors.
- The independent teacher passes 40 marked cases and 12
  tests; the neural model is entirely exact in 27/40
  Golden cases. Eight displays and ten inspected natural validation files are
  development evidence, separate from the first held-out test. Original-text and
  browser parity checks establish consistency, not semantic perfection.
