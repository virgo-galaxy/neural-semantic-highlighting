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
