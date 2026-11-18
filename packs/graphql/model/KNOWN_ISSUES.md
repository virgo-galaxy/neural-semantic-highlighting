# GraphQL known issues

- Natural test exact-span F1 is 96.36% on 14 bounded files;
  validation is 97.63% on 18. These different
  cohorts do not guarantee every SDL or operation feature.
- Enum value roles, argument versus input-property names, fragment references,
  type declarations/references and declaration/default-library modifiers can
  still be confused. Natural role scores/support are retained in test-metrics.
- Eight authored displays aggregate 97.60%,
  but Unicode block-string display is 80%. Long or unusual original strings,
  comments and escaped quotes can split or lose boundary roles across 512-byte
  windows. Strict Golden is only 10/24 whole cases including modifiers.
- No external schema/type validation, execution, resolver/network request,
  automatic language detection or highlighting inside strings is performed.
  Standalone source files are covered; JavaScript tagged GraphQL literals do
  not automatically dispatch to this model. Markdown reuse depends on its
  predicted fence region and a registered child model.
- Parser acceptance is offline supervision, not neural runtime correctness.
  The rejected joint decoder remains recorded rather than masking its visible
  enum/Schema regressions with an aggregate score. All source text is preserved
  even when the neural role is missed.
