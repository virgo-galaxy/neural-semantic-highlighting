# CSS family training

CSS, SCSS and Less share one 894,227-parameter byte Transformer: 512-byte context,
four layers, width 128, four heads, FFN 512, three BIO classes, 15 semantic roles
and one declaration modifier. The architecture follows the existing Go/TS family.
By default the model starts with new CSS weights. An explicit `--init-from-go`
experiment can copy the compatible Go byte/BIO backbone and semantic head rows
matched by label name; CSS-only roles retain their fresh initialization. Use a
full checkpoint under `artifacts/go`, never a selected inference artifact.
This starts a new CSS run with fresh optimizer, sampler, RNG and selection state;
it is distinct from `--resume`. Source weights are read-only and their hash,
epoch, dataset and copied labels remain in every descendant CSS checkpoint.

## Short iterations

Run from the repository root with the existing Python/PyTorch environment:

```bash
make train-css-smoke
make train-css CSS_EPOCHS=3
make continue-css CSS_CHECKPOINT=artifacts/css/<run>/last.pt CSS_EPOCHS=3
.venv/bin/python -m training.css.train --init-from-go artifacts/go/<run>/best.pt --epochs 3
```

The smoke run performs at most eight batches, evaluates complete validation
documents from each syntax, reloads its checkpoint, and checks pure-neural
whole-document inference. It never evaluates held-out test. Smoke success is
an execution check, not an accuracy claim or a promotable inference model.

Normal runs default to three additional epochs per invocation, batch size 32,
AdamW at 0.0003 with weight decay 0.01, gradient norm clipping at 1.0, modifier
loss coefficient 0.1 and modifier threshold 0.60. Resume retains model, optimizer,
loss weights, RNG, dataset identity, sampler, global epoch and patience counters.
Changing a resume configuration fails instead of silently starting a new setup.

The sampler cycles shuffled windows from each document kind to balance CSS,
SCSS and Less. Repeated presentations are recorded as repetitions, not new data.
Loss weights are computed from each unique training window once. Continuation
bytes/padding are ignored; modifiers are supervised only at Gold BEGIN positions.
The reader memory-maps prepared columns and creates tensors for the current batch.

## Validation and selection

Every completed epoch validates complete documents using fixed character-safe
windows, reassembled before span decoding. Evaluation cuts never consult Gold.
Reports show each syntax separately, as well as per-role and modifier metrics.
Selection uses the mean of CSS/SCSS/Less exact-span macro F1, so a large syntax
corpus cannot hide a weak smaller one. Patience is five epochs without improvement.
An early stop is a plateau signal, not proof that every use case is solved.

Before promotion, evaluate the actual predicted-adaptive-cursor runtime:

```bash
make evaluate-css CSS_CHECKPOINT=artifacts/css/<run>/best.pt
```

This defaults to validation and writes a new timestamped report. Reserve the test
split for final independent evaluation of a selected candidate. Match means exact
document/start/end/type; modifier-aware span metrics are reported separately.
Missing Gold support remains a coverage gap. Use real source diagnostics and
acceptable, documented limits to decide when further iterations have low value.

## Local outputs and runtime

```text
artifacts/css/
  smoke-<timestamp>/
  context512-<timestamp>/
    run.json
    invocations/<timestamp>.json
    status.json
    epochs/epoch-0001.json
    best.pt
    last.pt
```

Checkpoints and metadata are atomic. A run lock rejects concurrent writers.
Existing runs cannot be overwritten by a fresh invocation. An interruption
preserves the last completed checkpoint; a partial epoch may need repeating.
Each invocation records code hashes, Git state, device, data identity and budget.
Keep console logs alongside the run when launching a longer command.

`caffeinate -i` can wrap a training command to prevent idle sleep during that
process. Use short observed runs first. Give a measured time range before a long
run; scheduled monitoring and automatic notifications are not part of this workflow.
Keep the Mac powered and open. Do not depend on chat uptime as checkpoint storage.

`packs/css/runtime/local.py` implements the existing persistent JSONL process
protocol. It receives source and a document kind and returns UTF-16 semantic spans.
It invokes no CSS/Sass/Less parser, compiler, scanner, language server or subprocess.
Sass imports and Less JavaScript/plugins are never executed during inference.
Use an explicit development checkpoint until a model is selected:

```bash
.venv/bin/python -m packs.css.runtime.local \
  --checkpoint artifacts/css/<run>/best.pt --stdio
```

The selected `packs/css/model/model.pt` is reserved for a reviewed inference-only
export with matching metadata, reports and known issues; never resume from it.
