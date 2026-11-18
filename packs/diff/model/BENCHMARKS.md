# Diff/Patch baseline evaluation

Exact-span F1 requires identical original UTF-16 start/end and line role. It is
not character accuracy, patch applicability or nested programming-language
accuracy. Natural, authored focus, visible and strict Golden evidence are separate.

| Evidence               | Stream  | Documents | Exact-span F1 | Role macro F1 | F1 with modifiers |
| ---------------------- | ------- | --------: | ------------: | ------------: | ----------------: |
| Validation             | natural |        16 |        97.84% |        97.92% |            97.84% |
| Validation             | focus   |        80 |        96.29% |        93.97% |            96.29% |
| First independent test | natural |        26 |        98.03% |        97.52% |            98.03% |
| First independent test | focus   |        95 |        92.15% |        93.72% |            92.15% |

Primary: **98.03% on 26 first independent real patches**.
Validation remains separate: 97.84% on 16.
Eight authored displays aggregate 94.44%:
changes.diff 100.00%; long-line.diff 42.86%; mail.patch 100.00%; multi-file.diff 100.00%; new-file.patch 100.00%; no-newline.patch 100.00%; rename.patch 100.00%; unicode.diff 100.00%. Strict neural Golden is 19/28 cases exact including modifiers,
with 87.89% base-span F1.
Per-role support and F1 are in the matching test report; no display/Golden score
substitutes for independent real-source accuracy.

## Source families and learning

98 commit/blob-pinned maintained patches come from Buildroot, OpenWrt, vcpkg,
Electron and the Python feedstock. Production package/port/application patch
roots are metadata-whitelisted; entire dependency or patch-series families are
assigned before capture or predictions. Original patches and repository notices
are preserved, without asserting a blanket license for every upstream change.
Two unsupported originals and ten authored CRLF binary-notice tasks are retained
in quarantine. Existing Git rejects the latter on its path-header parsing.
Exact/lexical/shape copies crossing families are excluded by the unchanged shared
pipeline. No filters or reference labels are relaxed for a score target.

Original curriculum is 660 structural tasks, then 320 mixed metadata contexts:
header-only shapes had been excluded across families. Another 160 original
boundary/path tasks repair the observed absence of no-newline markers after
copy filtering. All previous retained family assignments and every natural
source/label/split remain identical. The final configuration requires at least
two training families for each critical feature; no-newline has four. Both
extension audits and all preceding snapshots/runs remain preserved.

| Split      | Natural patches | Focus tasks | Windows |
| ---------- | --------------: | ----------: | ------: |
| train      |              54 |         725 |    1153 |
| validation |              16 |          80 |     237 |
| test       |              26 |          95 |     267 |

Selected snapshot `61681476e9cb2d0724e11b597eece8e8ff0be92600cd20089ac5954eed78669b`; manifest SHA-256
`1620d93b3e4275a4f88482fba8ca82ae9ec2ff209ff7285993e8181e9e3d55b9`. Four layers, width 128, four heads, FFN 512,
five-byte learned local residual and 512-byte context have
**893,963 parameters**. Compatible weights come from the full
Markdown `artifacts/markdown/optimization-20261116/calibrated-fences-e3.pt`, not
inference models. Smoke precedes bounded short stages. 26 non-smoke epochs
take 202.2 seconds; full invocations and timings are retained.

Selected full checkpoint `artifacts/diff/context512-boundaries-20261119-01/candidates/epoch-0006-best.pt`, epoch 6, SHA-256
`836ad91f84d652bd94b14901238f8bd9bec790f5370ebff6b71a3c54a6440065`. Highest final-stage fixed natural validation role macro
F1 selects the candidate, followed by actual adaptive/visible/Golden review.
[Freeze](reports/selection.json) precedes the first independent test. No subsequent
training, fitting or selection uses that test. The existing greedy decoder uses
mean neural role logits and source-blind touching-span union. Validation-only
span-start aggregation and train-fitted joint BIO trials remain retained as
rejected diagnostics: they worsened natural or visible evidence. No runtime
parser, regex, prefix repair, count fixer or language guessing is introduced.

## Oracle and consumer scope

The checked original-coordinate walker is independently cross-checked by existing
git version 2.54.0 (Apple Git-157) in `apply --numstat -z --no-index --allow-empty` mode.
It only reports statistics: no patch application, working-tree file loading,
source/hook execution, new SDK or global dependency installation. Six teacher
tests and 28 separately marked cases pass. Original Unicode, BOM, CRLF, spaces,
tabs, hunk prefixes, paths and no-newline markers remain untouched. Source-label
and checkpoint provenance are bound at export; float32 ONNX conversion does not
quantize or retrain. Runtime/packaging parity remains separate from accuracy.
