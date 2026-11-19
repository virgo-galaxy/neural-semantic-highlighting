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
