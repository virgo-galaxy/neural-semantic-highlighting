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
