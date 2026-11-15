# .env known issues

- Natural test exact-span F1 is 98.25%
  across 3 files; role macro F1 is
  93.73%. Bounded family holdouts limit
  generalization claims. Parser acceptance is not project/schema validity.
- Quoted/multiline boundaries remain a measured weakness (multiline.env display 81.82% F1), including assignment/hash-looking content within values; individual comment/value boundaries can still split (comments.env 93.33%). Declaration flags, escaped quotes and long bodies remain approximate. One common ASCII-name/equals-assignment dotenv profile is supported; loader-specific colon/dotted/dashed names are outside the teacher contract. All values remain strings. No expansion, command substitution, environment injection, decryption, application validation or runtime parser/spelling repair is provided.
- Binding declarations, quotes and multiline value boundaries can have incorrect
  roles. Context is 512 original UTF-8 bytes; long/nested content and
  Unicode can split boundaries. No parser or spelling-based runtime fix hides these errors.
- The independent teacher passes 40 marked cases and 12
  tests; the neural model is entirely exact in 21/40
  Golden cases. Eight displays and 3 inspected natural validation files are
  development evidence, separate from the first held-out test. Original-text and
  browser parity checks establish consistency, not semantic perfection.
