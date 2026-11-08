# HTML training

Use the same small-model workflow as the existing packs: 512 UTF-8 bytes, four
Transformer layers, width 128, four heads and FFN 512. The base HTML model has
893,711 parameters, 11 markup/body roles and one closing-tag modifier. Its compact
`model-schema.json` is distinct from the public schema reserved for composition.

```bash
make train-html-smoke
make train-html HTML_INIT_FROM=artifacts/css/<run>/best.pt HTML_EPOCHS=3
make continue-html HTML_CHECKPOINT=artifacts/html/<run>/last.pt HTML_EPOCHS=3
make evaluate-html HTML_CHECKPOINT=artifacts/html/<run>/best.pt
make evaluate-html-composed HTML_CHECKPOINT=artifacts/html/<run>/best.pt
make challenge-html HTML_CHECKPOINT=artifacts/html/<run>/best.pt
```

Without explicit initialization, weights start fresh. `HTML_INIT_FROM` requires a
full compatible CSS/Go/HTML training checkpoint, copies shared backbone/BIO
weights and head rows by semantic name, and starts a new HTML optimizer, sampler,
RNG, selection history and loss weights. New roles/modifiers retain fresh weights.
Never initialize or resume from selected inference artifacts. Resume uses the
same run's `last.pt` and immutable dataset, restoring optimizer/RNG/state exactly
on the same backend; it cannot silently fork or alter configuration.

Defaults are three additional epochs, batch 32, AdamW 0.0003, weight decay 0.01,
clip norm 1.0, modifier loss weight 0.1, threshold 0.60, seed 42 and patience five.
Each natural window is shuffled/presented once per epoch. A bounded focus batch
of 16 grammar-curriculum windows follows each natural batch; the curriculum order
rotates across epochs, rather than replacing real-source training or counting
repetitions as new data. Earlier runs retain their recorded sampler on resume.
Loss weights
count unique train labels; padding/UTF-8 continuation bytes are masked and
modifiers are supervised only at Gold span beginnings.

Validation reassembles fixed, character-safe windows before whole-document
decoding; it never uses Gold cuts. Selection uses natural real-source validation
exact-span macro F1. Focus scores are reported separately.
Independent adaptive evaluation and Golden probes use actual neural cursor cuts.
Adjacent body predictions of the same neural role are coalesced by the decoder;
this does not parse or recognize any source language spelling.

Reports separately expose markup roles, source feature groups, exact body regions
and UTF-16 body coverage per JavaScript/CSS/data role. These are base-model scores,
not an evaluation of JS/CSS semantic predictions composed inside those regions.
The separate composed evaluator exercises `SemanticPack` orchestration through
three persistent neural model processes. Only predicted HTML body roles select
child inputs. Offline reference Gold composes the existing HTML/JS/CSS labelers,
quarantining unsupported child syntax with explicit counts. It freezes the HTML
candidate bytes, binds all three model hashes, keeps natural/focus reports separate
and never passes Gold regions to inference. Its scope excludes attribute snippets.
Reserve held-out test for one frozen reviewed candidate; inspect zero-support
categories and real-source failures rather than chasing the aggregate score.

Run metadata, invocation/code hashes, epoch reports, atomic status and full
`best.pt`/`last.pt` live under `artifacts/html/<run>`. Dataset snapshots remain
external under `NSH_DATASET_ROOT/html`. Failed/interrupted epochs preserve the
previous completed checkpoint; run locks reject concurrent writers.

Use `caffeinate -i` around observed local training commands, with durable console
logs. Give measured estimates before longer runs; do not add scheduled monitors
or notifications. Keep the Mac powered and open. Ordinary runs remain short
until data quality, resume behavior and useful validation improvements justify
more time.

The local runtime can inspect an explicit development checkpoint before any model
is selected. A reviewed inference export requires matching held-out adaptive
evidence, base/region scope, README, benchmarks and known issues; it strips
optimizer/RNG state and refuses to replace an existing selected artifact.
