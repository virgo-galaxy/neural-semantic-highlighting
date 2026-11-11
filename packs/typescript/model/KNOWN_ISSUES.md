# Known issues and follow-up plan

These are limits of the selected epoch 44, not reasons to delete tools or silently change labels. Follow-up items below are proposals; no additional training, heuristic correction or architecture change was made while exporting this model.

## 1. RegExp range and classification errors

**Evidence:** challenge F1 0.6133; positive exact 54/100; negative clean 59/60. [Raw report](reports/regexp-challenge.json).

The saved examples include delimiter/trailing-punctuation overrun and fragmented RegExp predictions. Examples are preserved from the report, not reconstructed training targets:

| Case                  | Expected RegExp | Reported overlapping prediction |
| --------------------- | --------------- | ------------------------------- |
| `positive-basic-005`  | `"/foo/s"`      | `"/foo/s;"`                     |
| `positive-basic-014`  | `"/a{2,4}/"`    | `"/a"`                          |
| `positive-escape-002` | `"/\\d+/"`      | `"/\\d+/;"`                     |
| `positive-escape-003` | `"/\\w+/"`      | `"/\\w+/;"`                     |

**Impact:** punctuation can receive RegExp styling; one expression may produce several semantic spans. Identically styled adjacent fragments may be visually less disruptive than a type/range overrun, but that visual effect has not been measured.

**Next verification:** group reported failures by range overrun, internal fragments and wrong type; inspect boundary/type logits and Gold label construction on development cases. Add targeted training data only after a small validation experiment supports it. Do not assume a semicolon-trimming rule or a larger context fixes all failures. Keep slash negatives in the acceptance suite and check that a fix does not degrade ordinary code.

## 2. Comment precision is a measured weak spot

**Evidence:** test Comment P/R/F1 = 0.8762 / 0.9626 / 0.9173, support 294.

**Unknown:** the aggregate table does not identify the root cause or affected source files. Do not label this as proved boundary failure or proved regression against a different test split.

**Next verification:** collect comment false positives and range errors from the error-analysis tool, replay ordinary code-block examples, then decide whether labeling, decoding or data coverage needs adjustment. Accept a fix only with a consistent evaluation setup and no important regressions.

## 3. String interiors and window boundaries are not infallible

**Evidence:** 251/26034 Gold string interior positions were not predicted I (0.9641%). B/O winners: 100/151. [Raw diagnostic](reports/string-fragmentation-test.json).

The runtime cursor uses predicted boundaries and only commits the selected prefix. It has no oracle boundary labels or persistent semantic memory of earlier windows. It protects UTF-8 cut positions and forward progress, but cannot guarantee correct semantic cuts or fit a single object longer than the context.

**Next verification:** inspect user-visible errors in real code blocks; distinguish harmless same-style splitting from lost string styling or bleeding into following code. Preserve these cases as diagnostics. Do not automatically restore old hard-string curricula or increase context solely to drive this diagnostic to zero. Extremely large embedded text is not a prerequisite for the first product integration, but failures must remain documented.

## 4. Context can help or hurt RegExp predictions

**Evidence:** on 40 pairs, context rescued 6 and hurt 3; 4 remained wrong in both forms.

**Next verification:** compare paired failures with identical patterns, decoder and weights. All these examples fit the current context, so this report does not attribute the remaining errors to a 512-byte limit.

## 5. Coverage and Modifier evidence are incomplete

There are no positive test spans for `enum`, `enum-member`, `label`, `decorator`. Several categories have very small support; `constructor` has 1 and `regexp` has 10. There is no per-document-kind breakdown proving all manifest entries equally strong.

The checkpoint's validation Modifier F1 is 0.9791, evaluated at Gold BEGIN positions. The whole-document test report does **not** score modifiers. Better Modifier numbers from other epochs must not be attributed to this artifact.

**Next verification:** retain fixtures, expand targeted coverage where product usage requires it, and add end-to-end Modifier evaluation on predicted spans. Use validation/development cases for changes; do not repeatedly tune to a frozen final test while calling it unseen.

## 6. Historical provenance and current delivery

The supplied reports do not embed model SHA-256 or corpus/split fingerprints. The original training commit, environment lock and complete training-data provenance were not supplied. The export binds the files now; it cannot recreate missing historical evidence. Licensing information was not supplied either and is not fabricated here.

The original native export review did not include browser delivery. The selected
weights have since been exported to ONNX and integrated into `@nsh/highlighter`
and the browser Playground, without a Python provider or remote inference service.
[Browser verification](../../../docs/browser-runtime.md) records export hashes,
numerical checks, exact-output comparisons and independent package integration.
It does not reconstruct the missing historical training provenance above, establish
cross-device latency/throughput/peak-memory benchmarks or complete a public-distribution
license audit.

**Next work:** measure real product behavior and device/network performance, and
record model/code/data hashes in future evaluations. Keep Core, renderer and themes
independent of this model's training implementation. Schedule model changes from
observed product impact rather than a requirement to obtain 1.0000 on every metric.
