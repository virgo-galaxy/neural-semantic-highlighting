# Model quality optimization

This work preserves the selected models, external datasets and full experiments.
The target is 95% natural exact-span F1 where practical, with 90% as the minimum
desired result. Targets are not promises or substitutes for measured evidence.

First review BAT/CMD, Perl, Shell dialects, XML (while retaining SVG quality),
Ruby, Python, SQL dialects, Svelte, Scala and INI. Also review the existing JS/TS
regular-expression, comment and long-string challenges against real TSX usage.

Start with bounded weights-only transfers from the selected **full** checkpoints
in `artifacts`, retaining schemas and frozen source-family assignments. Compare
the historical backbone with the existing learned adjacent-byte residual and
optional train-fitted joint BIO/role decoding. Decoder transitions use natural
training Gold; candidate selection uses natural validation by profile. The
unchanged decoder is a candidate, so calibration can be rejected.

Historical runs retain their mean profile role-macro selection. New targeted
experiments explicitly record `profile-f1` or `minimum-profile-f1` in training
configuration, so the 90/95% exact-span target and individual dialects participate
directly in validation selection. Natural-only class weighting is another recorded
experiment option. Roles, Gold, held-out membership and scoring do not change.
Role macro F1, modifiers, Golden and actual failures are still reviewed before
promotion; higher aggregate F1 alone is insufficient.

Inspect remaining validation failures before adding narrowly targeted training
coverage. Never put Golden, Playground or held-out test code into training.
The already inspected natural tests are exposed regression evidence. New
source-family holdouts must be frozen separately before later training, and
fresh scores must remain separate from historical regression scores.

Promote only reviewed candidates, archive preceding inference bundles, export
browser models, verify native/browser parity and consumer behavior, and update
the README with actual scores and remaining limitations. Unsuccessful experiments
stay in ignored artifacts and do not replace a better selected model.

Additional bounded source captures are explicit opt-in steps, without SDK installs:
`python -m packs.perl.dataset.capture_quality` and
`python -m packs.python.dataset.capture_quality`. The latter uses the already
available CPython 3.15 source tree and installed package metadata, copies original
licenses, and never imports/executes collected modules. Each collector freezes
paths and family folds before capture; prior configurations live under
`packs/<pack>/dataset/history/`. Rebuild the usual collect/label/validate/prepare
steps after capture. BAT's `generate_quality` projects only natural TRAIN source
into case variants in the same family/fold; validation/test bytes remain unchanged.

Optional learned relative-distance slopes retain the 512-byte architecture and
all parent tensors at transfer time. BAT-only ASCII embedding tying encodes case
invariance in trained weights without normalizing runtime text. These are
measured candidate experiments, not guarantees that every pack reaches 90/95%.

Shell's additional source-only capture is `make dataset-bash-quality-sources`.
It freezes at most 96 existing macOS Zsh 5.9 function paths, excludes the original
named families, retains upstream licensing and per-file notices, and never runs
the captured functions. One duplicate is excluded by the usual dataset builder.
All 4,423 original prepared documents retain source, Gold and fold membership.

## JS/TS refinement recipe

`node --import tsx packs/typescript/dataset/generate-quality.ts` writes a new,
versioned external focus corpus, preserving previous versions. Compiler-AST Gold,
syntax-only RegExp construction, fixed context-family folds, EOF/newline variants
and real slash negatives are recorded in its manifest. No input source is run.

```sh
PYTHONPATH=. caffeinate -i .venv/bin/python training/typescript/refine.py \
  --init-from artifacts/typescript/<full-run>/best.pt --local-kernel 5 \
  --focus /absolute/path/to/versioned/focus.json --eof-loss-weight 8 \
  --run artifacts/typescript/<new-run> --epochs 4
# Resume this same refinement run (not the legacy trainer):
PYTHONPATH=. caffeinate -i .venv/bin/python training/typescript/refine.py \
  --resume artifacts/typescript/<new-run>/last.pt --local-kernel 5 \
  --focus /absolute/path/to/versioned/focus.json --eof-loss-weight 8 \
  --run artifacts/typescript/<new-run> --epochs 4
```

This uses deterministic 100-RegExp/200-other TRAIN-document replay. All natural
validation files and authored validation contexts remain outside the optimizer.
The unchanged initial weights are eligible for selection; micro/macro natural
regression guards constrain focused gains. Optional EOF loss weighting only uses
true document-end positions, never source spelling or Gold token roles. Runtime
consumes the original text without appending a newline or repairing punctuation.
The historical RegExp challenge is exposed development evidence, separately from
filtered authored holdouts and 24 read-only real Virgo Design TSX test files.

A validation-only windowing stage also compares the unchanged cursor with bounded
overlapping logit fusion. It addresses edge-dependent predictions without editing
source, changing labels, increasing model context or adding a parser. Its policy
and report hashes travel with native/browser bundles. Short snippets retain the
existing path; long documents require additional model windows. Original tests
remain exposed regression evidence after this development review.

Ruby's `make dataset-ruby-quality-sources` adds 64 metadata-selected files at the
already pinned upstream commits, checking Git blobs and copying original licenses.
The original family function and all 1,657 prepared documents retain their Gold
and folds; duplicate exclusion leaves 40 additional training, three validation and
11 held-out natural files. It installs no Ruby runtime. XML's
`make dataset-xml-quality-curriculum` adds separately grouped long opaque-content
tasks while preserving all 2,964 earlier prepared documents. These focus tasks do
not substitute for natural XML/SVG measurements or change their Gold.

## Reporting and release acceptance

Release tables compare the same exposed historical natural-source cohort before
and after. Additional frozen families remain separate, including results below
90%; a pooled or authored score never replaces them. The later window revision
reuses Python/BAT additional tests after their first read, explicitly labelled as
exposed follow-up evidence. Perl's additional 16 files are first read after final
validation-only window selection. Golden, role macro and individual profiles
remain acceptance checks alongside micro F1. A worse candidate can be rejected.

Selection reports in inference bundles contain compact search tables and their
full immutable experiment-report hashes; repeated matrices and complete role
diagnostics remain in ignored `artifacts/quality-20261119`. Dated native/browser
bundles retain all original files and hashes. No distribution, visibility change
or external push is part of this optimization.

## Reviewed results (2026-11-19)

All 40 packs were included in browser regression. This revision updates 24 selected
model/decoder/window bundles; the same historical source cohorts are compared
below. Different languages have different corpora and scopes. These are exposed
regressions, not 24 new independent tests.

| Name       | Same historical files | Before F1 | Selected F1 |
| ---------- | --------------------: | --------: | ----------: |
| bash       |                    11 |    84.78% |      87.12% |
| bat        |                     3 |    74.29% |      90.61% |
| c          |                    18 |    93.90% |      94.60% |
| cpp        |                    14 |    92.67% |      94.16% |
| csharp     |                    24 |    94.64% |      95.53% |
| dart       |                    20 |    94.22% |      95.07% |
| ini        |                     8 |    89.70% |      96.93% |
| java       |                    29 |    92.60% |      93.59% |
| kotlin     |                    31 |    94.57% |      96.28% |
| lua        |                    15 |    91.78% |      94.36% |
| makefile   |                    17 |    92.87% |      94.12% |
| perl       |                     4 |    83.60% |      91.00% |
| php        |                    21 |    94.05% |      95.55% |
| powershell |                     3 |    90.67% |      91.96% |
| python     |                     4 |    87.52% |      91.48% |
| ruby       |                    15 |    86.96% |      90.60% |
| rust       |                    15 |    94.90% |      95.93% |
| scala      |                    30 |    89.00% |      90.23% |
| sql        |                     7 |    88.41% |      90.08% |
| svelte     |                     9 |    88.47% |      91.41% |
| swift      |                    22 |    93.65% |      94.52% |
| typescript |                    50 |    99.31% |      99.45% |
| xml        |                     7 |    85.87% |      87.72% |
| zig        |                    21 |    92.51% |      93.65% |

The 95% target is not reached everywhere. XML remains **87.72%**, despite comment
F1 improving from 51.28% to **85.71%**. SVG remains 100% on six bounded files.
Shell's legacy overall result is **87.12%**; Bash is **94.29%**, and the additional
12 Zsh function files reach **90.91%**. Bash strict Golden pass/fail states are
unchanged. XML/Shell therefore still fall below the desired overall 90% floor.
SQL's pooled 90.08% must not conceal weaker MySQL coverage.

Additional cohorts remain separate: Python 19 files **90.87%**, Ruby 11 files
**94.41%**, Perl 16 files **88.33%**, and BAT six harder project files **75.36%**.
Python/BAT are now exposed follow-up evidence, and Perl/Ruby were first read only
after their final validation-selected weights/window policy. These scopes cannot
be replaced by the better historical percentages. Makefile's earlier 16-file
additional cohort is now an exposed regression at **94.57%**, while its original
17-file cohort reaches **94.12%**.

JS/TS's RegExp development challenge improves **61.33% → 93.27%**, with a precision
tradeoff (54/60 negative cases clean versus 59/60 before). First-read authored
RegExp holdout F1 is **96.48%**; real read-only Virgo Design TSX is **99.39%** across
24 files. A small product-comment regression remains recorded. No product source
was executed, modified or put into training.

C, Zig and Dart reject larger regressions in calibrated/fine-tuned candidates and
retain the original neural weights with validated window improvements. Makefile
also keeps its original weights/decoder: the fine-tuned candidate regressed
inline recipes and no-final-newline probes. The selected window revision keeps
all 26 previously exact Golden cases. INI's selected decoder retains its original
weights. Short snippets continue to use their existing single-window path.

Final verification: **182 frontend tests**, **36 shared training tests**, and
**410/410 browser/native matches**. The independently installed local npm tarballs
also produce **410/410 matches** in a production build served by a temporary
GET-only static server, with all 40 selected ONNX assets verified and no Python
inference service or workspace alias. The full project check passes with two
pre-existing Go version-locked cases explicitly skipped (`TestFocusedCorpusReplay`
and `TestModulePipelineOffline`): Gold requires 1.27.1 and the installed toolchain
is 1.27.4; no toolchain was installed.

All **85 original weight files** are preserved byte-for-byte, at their preceding
paths or dated bundle archives. Complete external data, immutable reports and
training checkpoints remain intact. The repository/packages stay private; this
work does not publish or push. [Machine-readable results](quality-optimization-results.json)
record selected asset hashes, cohort values and verification details.
