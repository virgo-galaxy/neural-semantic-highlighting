# JS / TS measured limits

- RegExp precision remains imperfect: the exposed challenge has 14 false positives, including slash text, JSX and punctuation; 54/60 negative cases stay clean.
- Long comments/strings and context-dependent roles remain approximate with 512-byte context.
- The small real-product cohort has one comment-boundary regression (comment F1 91.67% versus 100% previously), despite aggregate TSX F1 improving to 99.39%.
- Authored holdouts, product files and archived tests have different scopes; their percentages are not interchangeable.
- Inference consumes original text in the browser worker or local runtime. No source execution, parser or spelling-based repair hides neural errors.
