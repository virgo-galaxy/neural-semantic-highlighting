# Perl measured limits

- **Multiple Here Documents can confuse context.** Standalone ordinary and
  indented forms work in the displayed examples. A measured file combining an
  ordinary block followed by an indented literal block misclassifies the second
  variable-first body as variables/operators/comments. Its full source and
  predictions remain in `reports/display-challenges.json`. Queued documents also
  have boundary errors. No runtime repair conceals this limitation.
- **Whole regions have imperfect boundaries.** POD, data sections, strings and
  Here Document terminators can split, overrun whitespace/CRLF or lose state past
  512 bytes. Interpolated quotes/bodies are opaque strings, not separately
  highlighted embedded expressions or foreign languages.
- **Name roles and modifiers remain approximate.** Golden `say`/`uc` can become
  keywords; builtin-shadow flags can be wrong. Barewords, hash keys, methods,
  namespaces and numeric defaults are source-local predictions, not execution or
  import resolution. Some operators and whitespace-adjacent literals are split.
- **Version breadth is bounded.** Natural source comes from host Perl 5.34 core;
  original signatures are represented as whole parameter regions. PPI is not a
  full Perl compiler. Experimental class/field syntax, exotic prototypes,
  source filters, dynamic code and Raku are not complete language support.
- **Sparse evidence matters.** Natural test F1/macro are 83.60%/64.07% on only four
  modules; focused test F1 is 88.21%, below visible simple examples. Stronger
  displayed snippets do not establish broad project accuracy. Preserve the first
  test and begin future work from actual code without calling reused tests unseen.
