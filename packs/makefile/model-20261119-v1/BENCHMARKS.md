# Makefile optimized evaluation

The unchanged metric requires identical original UTF-16 start/end and role;
modifiers are separate. No source text, labels, roles or old family assignments
change. The original 17-file test is exposed **legacy regression**. Sixteen new
source files, from complete families reserved before opening sources, provide
the new independent test. Both models are frozen before these fresh predictions.

| Evidence                  | Natural files | Baseline F1 | Optimized F1 | Optimized F1 with modifiers |
| ------------------------- | ------------: | ----------: | -----------: | --------------------------: |
| Fresh independent test    |            16 |      90.06% |       93.79% |                      93.27% |
| Exposed legacy regression |            17 |      89.14% |       92.87% |                      92.35% |

The same-cohort legacy improvement is **3.73 percentage points**.
Fresh baseline 90.06% and optimized
93.79% use identical newly held-out source/Gold. Results,
support and per-role counts are in [test metrics](reports/test-metrics.json) and
[baseline comparison](reports/baseline-comparison.json). Combined natural F1 is
93.39% on 33 files; it does not replace the fresh result.

## Validation and source review

| Natural validation | Files | Baseline F1 | Optimized F1 |
| ------------------ | ----: | ----------: | -----------: |
| all                |    25 |      82.66% |       86.39% |
| fresh              |    14 |      79.11% |       83.03% |
| legacy             |    11 |      86.94% |       90.44% |

Fresh validation is harder than the fresh test. In actual validation, zstd
recovery improves 70.27% → 95.08%, external sequence producer 76.06% → 99.04%,
and LZ4 examples 77.86% → 90.84%. Long banner comments, quote/space boundaries and
recipe/assignment roles improve. The Helm source with a distant custom SHELL
remains around 53%; bounded context and conservative opaque-shell supervision
remain material limits. Detailed [validation review](reports/validation-review.json)
retains every case and missing/unexpected spans.

Eight unchanged authored displays improve **95.54% → 96.90%**.
Function examples reach 100%, recipes 97.96%. Some small edge probes regress:
strict Golden **29/46 → 26/46**, base-span F1 **89.69% → 86.24%**;
Unicode display 96.15% → 92.31%, define display 90.00% → 87.80%. These are
retained limitations, not hidden by the aggregate real-source improvement.
Authored focus test is 98.46% on 180 tasks and remains separate.

## Immutable data and bounded learning

The [protocol](reports/optimization-protocol.json) fixes metadata-only hashes,
whole related families and the 90% target before opening added sources. Eight
additional official project trees and existing pinned trees yield 81 bounded
candidates from 12 projects; original blobs/licenses remain captured. Thirty
unsupported originals are quarantined; unchanged exact/lexical/shape exclusion
removes two further new copies. All prior retained documents/labels/assignments
remain identical. Final natural splits are **47 / 25 / 33**, including **19 / 14 /
16** new train/validation/test files. No holdout/exclusion rule is weakened.

A 16-family/320-task original context extension addresses validation error
categories without reading Golden, displays or test source. Actual binding/rule
counts define families; focus counts are **824 / 180 / 180**. Every earlier
snapshot/run remains retained. Selected snapshot `911784b91ed91dbf16806122790a31f920b78a265dfe3eed11d4807ee6b011a8`;
manifest SHA-256 `d500d36856f5ce21be8f91de09c61250a620ca0338d38039a2a6518bb844dc23`.

The four-layer width-128 backbone keeps context 512. Its existing zero-initialized
five-byte depthwise residual adds 768 learned parameters, totaling **894,479**.
Full `artifacts` checkpoints initialize short new runs; no inference model resumes
training. [Experiments](reports/experiments.json) retain **22 non-smoke epochs /
125.2 seconds**, smoke and all invocations. No optimizer update or fitting
follows the first fresh test.

Legal BIO/role transition matrices are fitted on 47 natural **training** sources
only. Validation selects a fixed grid, expanded at its validation-selected upper
boundary. Absolute-minimum trials and later balanced **F1 gain** selection remain
retained. Balanced selection guards all/fresh/legacy validation relative to the
same frozen baseline, with exact source-identity checks. All absolute cohort
scores stay visible. The selected source is `artifacts/makefile/optimization-20261118/contexts-e10-balanced.pt`, SHA-256
`556be927b35f06b506d7aa92d3ae122af2038bb92a9ccf8a8f33ab90beec9cb6`. [Calibration](reports/calibration.json) binds parameters,
protocol, source checkpoint, baseline validation and calibrator code. Optimizer
code provenance is unchanged; its historical calibrator source is archived.

The candidate/parameters and validation-only decision were fixed in the
prelaunch invocation. A Python serialization error prevented that invocation
from writing the selection record; it was corrected after evaluation launched
without reading any test prediction. [Selection](reports/selection.json)
explicitly preserves that recording issue; the candidate, weights and decision
never change after fresh results. Native/browser exports bind the exact test and
structured-decoder hashes; conversion is float32 without quantization/retraining.

The existing pinned offline grammar/Bash tools and every older model/data asset
remain preserved. No SDK/global dependency, Make execution, include loading or
runtime source parser/regex/spelling repair is introduced. The
[known limits](KNOWN_ISSUES.md) distinguish real accuracy from runtime parity.
