# Diff/Patch known issues

- Natural exact-span F1 is 98.03% on 26 first-test patches;
  validation is 97.84% on 16. Small bounded
  dependency/series cohorts do not guarantee every patch producer or feature.
- Very long lines can lose their addition/deletion/context role beyond 512-byte
  context; mean-logit voting and touching-span union do not reconstruct missing
  information. Header-like payloads, metadata, path/quote boundaries and newline
  markers can still be confused. Visible per-case errors are retained.
- Eight displays aggregate 94.44%; strict
  Golden is 19/28 whole cases exact including modifiers. These are visible
  development probes, not additional independent accuracy.
- Common unified/Git source and bounded headerless +/- fragments are the scope.
  Combined merge, normal/context and word-diff formats, ANSI terminal color,
  arbitrary archives or complete mail/patch-applicability validation are outside
  the baseline. Existing offline Git rejects some CRLF binary-notice forms;
  those original training candidates remain quarantined.
- Binary payloads and programming code inside changed lines stay opaque. No
  original file loading, embedded-language dispatch, patch application, Git/Python
  process, prefix parser or runtime source repair participates in highlighting.
  Markdown reuse still depends on its predicted fence and registered child model.
- Addition/deletion use theme foreground colors; original + and - signs remain
  non-color cues. Consumers may add backgrounds with ordinary semantic CSS.
  All original text remains intact even where a neural role is incorrect.
