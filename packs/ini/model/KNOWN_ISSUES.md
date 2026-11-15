# INI known issues

- Natural test exact-span F1 is 89.70%
  across 8 files; role macro F1 is
  90.88%. Bounded family holdouts limit
  generalization claims. Parser acceptance is not project/schema validity.
- Indented continuation lines resembling assignments or headers can split or gain property/punctuation roles (continuations.ini display 82.76% F1). Packaging constraints/version strings and empty-value continuations remain weaker (setup.cfg 89.47%); quoted/path values and section/glob boundaries can also fragment. Common INI/EditorConfig source uses one explicit dialect: #/; full-line comments, with inline value markers kept literal. Application-specific inline comments/escape rules and general .conf/.env syntax are outside scope. No interpolation, configuration execution, project validation or runtime parser/spelling repair is provided.
- Section/option names, continuations and value boundaries can have incorrect
  roles. Context is 512 original UTF-8 bytes; long/nested content and
  Unicode can split boundaries. No parser or spelling-based runtime fix hides these errors.
- The independent teacher passes 40 marked cases and 12
  tests; the neural model is entirely exact in 17/40
  Golden cases. Eight displays and 7 inspected natural validation files are
  development evidence, separate from the first held-out test. Original-text and
  browser parity checks establish consistency, not semantic perfection.
