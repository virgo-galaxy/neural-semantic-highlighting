# Protocol Buffers baseline evaluation

Exact-span F1 requires identical original UTF-16 start/end and semantic role.
Modifiers are separate. Natural, authored focus and visible evidence stay
separate; parser acceptance is not compiler correctness or neural accuracy.

| Evidence               | Stream                      | Documents | Exact-span F1 | Role macro F1 | F1 with modifiers |
| ---------------------- | --------------------------- | --------: | ------------: | ------------: | ----------------: |
| Validation             | natural                     |        13 |        98.04% |        98.65% |            97.51% |
| Validation             | focus                       |       100 |        97.52% |        83.15% |            96.74% |
| First independent test | natural                     |        24 |        98.94% |        96.68% |            98.45% |
| First independent test | focus                       |        80 |        98.39% |        98.30% |            98.21% |
| First independent test | fresh-primary-test          |        12 |        98.55% |        96.17% |            98.07% |
| First independent test | retained-natural-regression |        12 |        99.41% |        97.06% |            98.91% |

The final primary cohort is 12 fresh temporalio/api files, fixed test-only before
source capture. Earlier upstream test fixtures that passed the first path filter
are removed from formal natural data after actual validation review. Case-insensitive
path checks, a bounded production allowlist for protobuf core, unchanged logical
family cohorts and an old-non-test fingerprint audit prevent training/validation
leakage into the fresh test. Initial captures and exploratory runs remain preserved.

The primary result is **98.55% on 12 first independent natural
files**. Small family cohorts do not certify every proto version or feature.
Eight visible displays aggregate **99.77%**:
account.proto 100.00%; collections.proto 100.00%; editions.proto 100.00%; enum.proto 100.00%; extensions.proto 98.00%; options.proto 100.00%; service.proto 100.00%; unicode.proto 100.00%. Strict Golden is **23/26** whole cases exact including modifiers,
with **98.27%** base-span F1. No
Golden/display or test prediction supplies training labels or candidate selection.

## Fixed data and bounded training

83 bounded commit/blob-pinned original production `.proto` files across five
application/library projects are captured with licenses. Whole directory/package
families are fixed from metadata before reading source or predictions. The
original curriculum supplies 840 tasks in 42 distinct structural families. The
unchanged exact/lexical/shape exclusion removes copies crossing families; no
split, teacher contract or reference labels are relaxed for a score target.

| Split      | Natural documents | Focus tasks | Windows |
| ---------- | ----------------: | ----------: | ------: |
| train      |                37 |         620 |    1051 |
| validation |                13 |         100 |     221 |
| test       |                24 |          80 |     300 |

Final snapshot `9c016c154e6432ba20c88c10436ee9869d6c2f8c093849f6f8cf06d7801646d3`; manifest SHA-256
`76f078764f00aa2066938e95ebdf4219f63a291f19c928fee7efd67856c574f8`. All raw corpora, Gold, prepared revisions,
training checkpoints/optimizer/RNG and historical formal models remain intact.
The [metadata audit](reports/metadata-rebind-audit.json) records correction of an
inherited template version field to the actual grammar commit. A new isolated
tool build and Gold/prepared snapshot retain correct provenance; **in that metadata-only
republication all original
Gold source/span and prepared-file bytes remain exactly identical**. The final
production-source revision separately changes retained natural membership. The first
exploratory run is preserved; the selected stage binds the corrected snapshot.

Four layers, width 128, four attention heads, FFN 512, a five-byte local residual
and 512-byte context contain **894,995 parameters**. Fresh pack
stages initialize compatible weights from the preserved full selected GraphQL
artifacts checkpoint, never exported `.pt`/ONNX. Smoke verifies reload/inference;
28 non-smoke epochs take 298.1 seconds. Full [invocations and timings](reports/experiments.json)
remain recorded. No learning, calibration or candidate selection follows the
first independent test. The selected greedy decoder only uses logits and the
existing source-blind touching-string/comment policy; no syntax, regex, source
spelling, imported model or external environment influences inference.

The selected full checkpoint is `artifacts/protobuf/context512-production-20261119-01/candidates/epoch-0008-best.pt`, epoch 8,
SHA-256 `d7f0cd3bdfe9207e69abc955cf4c7ea8cd593a3b100e29fcee55e03f9964a511`. Highest final-run fixed natural validation role
macro F1 selects the epoch; actual adaptive natural validation, visible code and
Golden are inspected before [freeze](reports/selection.json) and first test.
Export binds matching independent test, schema/semantic/config/dataset identity.
Float32 ONNX conversion does not quantize or retrain.

## Offline parser and actual source review

Tree-sitter runtime 0.25.10 plus coder3101/tree-sitter-proto commit
`68a898a1715f1b0fce0d21ae6d1f4e24c60fcb2c` are original blob-pinned sources.
Existing Clang builds them only under ignored artifacts, with source/compiler/
binary checksums and original licenses. No SDK, protoc or global dependency is
installed. Parse-only CST ranges supply labels; no import loads, symbol resolution,
source execution or code generation occurs. Modern grammar covers edition
headers, visibility, option imports and bare reserved names, in addition to
common proto2/proto3 structures. This is not a full compiler/edition-feature checker.
Six teacher tests and 26 independently marked cases pass, preserving Unicode,
CRLF/BOM, original lexical strings and comments between concatenated values.
Reports retain all visible errors and ten inspected actual validation files.
All 81 preceding weight files remain byte-identical. The repo/packages stay
private; no dataset upload, publication or visibility change is made.
