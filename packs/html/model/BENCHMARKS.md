# HTML benchmark

## Protocol and results

Exact spans match original UTF-16 start/end and type; modifier-aware scoring also
matches the modifier set. Macro F1 averages roles with Gold or predicted support;
an unsupported predicted role scores zero. Unrepresented roles establish nothing.
No Gold cuts, runtime parsing or lexical repair guide adaptive inference.

| Scope                  |  Natural validation F1 / macro |        Natural test F1 / macro |
| ---------------------- | -----------------------------: | -----------------------------: |
| Base markup/body roles | 98.42% / 81.39% (11 documents) | 96.37% / 75.75% (10 documents) |
| Composed JS/CSS bodies | 97.93% / 89.79% (10 documents) |  96.53% / 90.04% (9 documents) |

Base test contains 1,423 Gold spans. Per-role F1: doctype 100%, string 98.05%,
punctuation 98.87%, tag 99.04%, attribute 97.01%, text 67.84%, entity 80% (two
references), JS body 50% (three bodies), CSS body 66.67% (two bodies), other-data
body 0% (one body). There are no HTML comments in this test. Validation has only
two comments and both fail exact boundaries. These small counts limit conclusions.

Natural whole-body exact test F1 is 45.45% (5 TP, 11 FP, 1 FN). Typed UTF-16 body
coverage F1 is JS 96.31%, CSS 99.76%, data 97.44%. Character coverage does not
establish exact region correctness. Validation body exact F1 is 80%, with typed
coverage JS 99.99% and CSS 98.95%; it has no data bodies. Raw body scores are
reported both by stream and pooled, keeping synthetic failures visible.

Composed reference Gold is produced offline by HTML, JS and CSS labelers. Actual
inference uses only neural predictions and existing selected child models. One
natural validation document (`glob-import/root/index.html`) and one natural test
document (`custom-select/index.html`) fail complete embedded reference coverage;
their exclusions and source identities are explicit in the reports. Base scoring
retains both. No reference regions are fed to inference and no missing Gold is
invented. Child hashes and evaluator/source hashes are archived with each report.

Focus validation/test scores are separate in the model README. The 10 independently
marked visible Golden probes are development checks, not a held-out accuracy
estimate: only four are entirely exact. The raw mismatch report is retained.
Playground demonstrations are not collected or used as training source.

## Frozen data and lineage

Prepared snapshot:
`6b817884ae7a25904db1fe5edba5f424d0f07f04da4a223fb6cf814cdc07c98c`.
Its manifest hash, checksums and directory-group assignments are archived.
The 554 successfully labeled inputs contain 194 collected real-source documents
and 360 original curriculum documents; three additional malformed real files
remain quarantined. There are 531 unique documents after 23 exact duplicates,
with 63 cross-directory lexical/shape copies excluded. The remaining 468 split
by intact source/template directories before windows:

| Split      | Natural documents / windows | Focus documents / windows |
| ---------- | --------------------------: | ------------------------: |
| Train      |                    95 / 358 |                 264 / 404 |
| Validation |                     11 / 43 |                   40 / 53 |
| Test       |                     10 / 43 |                   48 / 48 |

Local sources reuse Vite, TanStack Query and Redux Toolkit checkouts. Targeted MDN
HTML/Web Components/dialog/popover/shadow-DOM files are pinned in
`../dataset/git-sources.json`, verified by Git blob identities and SHA-256 locks,
with upstream root licenses preserved externally. No scripts or dependencies are
downloaded/executed as part of collection. Curriculum v3 mixes fragments and
documents, CRLF, typed data and short mixed bodies without reading Golden answers.
Curriculum variants remain grouped by family; template generalization is measured
separately from real source. Train contains every compact role; natural validation
lacks entities/data and natural test lacks comments, which remain coverage gaps.

The standard four-layer candidate at epoch 20 was chosen before test, using
real-source validation and actual failures. Its optional local-context comparator
uses the same snapshot, but is not selected. Earlier datasets differ in grouping
and must not be compared as a controlled improvement series. All full checkpoints
and historical immutable datasets remain preserved. The first test of each scope
was run only after freezing the selected candidate, on MPS. Reported evaluator
times include setup forward passes and are not browser latency benchmarks.

## Reproduce

```bash
make evaluate-html HTML_CHECKPOINT=artifacts/html/context512-fragments-20261108-01/best.pt HTML_DEVICE=mps
make evaluate-html-composed HTML_CHECKPOINT=artifacts/html/context512-fragments-20261108-01/best.pt HTML_DEVICE=mps
make challenge-html HTML_CHECKPOINT=artifacts/html/context512-fragments-20261108-01/best.pt HTML_DEVICE=cpu
```

Use the frozen external snapshot and original checkpoint for checkpoint-bound
reports. Test reports in this bundle are the first independent test, not a tuning
target. The inference-export hash differs from the full training-checkpoint hash.
