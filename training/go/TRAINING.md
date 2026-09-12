# Go Baseline Training

This is the first trainable Go implementation, not a selected production model.
It consumes the existing prepared snapshot; it does not collect modules, relabel
Gold, rebuild windows, or alter the TypeScript model. All commands below run from
the repository root, using the existing `.venv/bin/python` and its PyTorch install.

## Start with a smoke run

```bash
make check
make train-go-smoke
```

The default smoke run performs at most eight natural batches and one focused batch,
then evaluates a small set of **complete validation documents**, reloads its saved
checkpoint, compares reloaded inference logits, and predicts a validation source
using the adaptive cursor. It never opens the held-out test files. The final line
starts with `SMOKE PASS` only when those checks actually complete. It is an execution
check, not an accuracy gate, and low smoke F1 is not a reason to recollect data.

The snapshot pointer is resolved once at startup. Its manifest, ordered schema,
quality gate, and selected split file checksums are checked before use. The run
records the full snapshot identity and manifest hash. A corrupt, incompatible,
or previously unbalanced snapshot is rejected rather than silently accepted.
The reader memory-maps binary columns and converts one batch at a time. Validation
source text is loaded only for the requested split; the corpus is not loaded as
one giant training tensor. The final partial batch is retained.

The default device policy is MPS, then CUDA, then CPU according to availability.
The selected device and PyTorch version are printed. Override explicitly when needed:

```bash
make train-go-smoke GO_DEVICE=mps
make train-go-smoke GO_DEVICE=cpu GO_BATCH_SIZE=16 GO_FOCUS_BATCH_SIZE=8
```

An explicitly unavailable accelerator fails clearly. There is no silent device
fallback after an out-of-memory error, no global package installation, no saved
environment mutation, and no automatic enabling of unsupported-operation fallback.
CPU thread settings affect only this Python process. No DataLoader workers are
spawned and no inherited mmap handles are sent to subprocesses on macOS.

## First short baseline run

After smoke verification:

```bash
make train-go
```

This creates a **new** run, not a continuation of smoke weights. The default budget
is **three additional epochs**, with early stopping after five epochs without
improvement in natural validation exact-span F1. This is an iteration budget,
not a promise that a model is finished after three epochs. Inspect the per-epoch
report before extending the same run; do not start from scratch to add more epochs. Model parameters start from random initialization;
TypeScript checkpoint weights are not loaded. The architecture follows the same
small byte-transformer family:

| Setting                            | Default                                              |
| ---------------------------------- | ---------------------------------------------------- |
| Context                            | 512 UTF-8 bytes, not BPE tokens or characters        |
| Byte vocabulary                    | 0-255, plus padding id 256                           |
| Transformer                        | 4 layers, width 128, 4 heads, feed-forward width 512 |
| Dropout                            | 0.1                                                  |
| Boundary head                      | outside / begin / inside                             |
| Semantic heads                     | Go schema order: 16 token types, 3 modifiers         |
| Parameters with the current schema | 894,614                                              |
| Optimizer                          | AdamW, learning rate 0.0003, weight decay 0.01       |
| Gradient norm clipping             | 1.0                                                  |
| Natural batch size                 | 32                                                   |
| Focus batch size                   | 16                                                   |
| Focus scheduling                   | one focused batch per 8 natural batches              |
| Modifier loss coefficient          | 0.1                                                  |
| Modifier prediction threshold      | 0.60                                                 |

These are explicit baseline defaults, not established optimal Go hyperparameters.
The head sizes are read from the validated schema, not from TypeScript constants.
Each encoder layer is initialized independently. Batches are trimmed to the longest
actual byte sequence in that batch, retaining padding masks for shorter rows.

```bash
make train-go GO_EPOCHS=3 GO_BATCH_SIZE=32 GO_FOCUS_EVERY=8
```

Full training shuffles each natural training window once per epoch, without
replacement. Focused **training** windows are separately shuffled and cycled;
each focused window is revisited as required by the focus schedule. A final focus
batch also follows an incomplete natural interval. With 37,754 natural windows,
batch sizes 32/16, and an interval of eight, this gives 1,180 natural batches and
148 focused batches per full epoch: 37,754 natural and 2,368 focused presentations.
The 2,368 presentations are repeated sampling, not 2,368 independent focused examples.
Validation and test focus windows are never sampled for optimization.

Boundary and type losses ignore padding and UTF-8 continuation bytes. Type loss
also ignores outside positions. Modifier BCE is evaluated only at Gold span
beginnings, including negative examples at beginnings with no modifier. An INSIDE
position is not an all-negative modifier example. Capped inverse-square-root class
weights and modifier positive weights are computed only from training labels,
counting each original training window once; those weights are saved in checkpoints.
Natural/focused training losses and presentation counts are reported separately.

## Console format and iteration budget

The Go console now follows the TypeScript training layout. It is plain text, so
copied terminal output and redirected logs contain the same information. All log
messages, comments, and documentation remain English.

At startup, the trainer prints the requested **additional** epoch budget, global
epoch range, natural/focus batch sizes, optimizer steps per epoch, and planned
optimizer steps for this invocation. The default is three epochs for both
`make train-go` and `make continue-go`, and one for smoke. Override explicitly:

```bash
make train-go GO_EPOCHS=1
make continue-go GO_CHECKPOINT=artifacts/go/context512-RUN/last.pt GO_EPOCHS=3
```

Use the actual checkpoint path for `RUN`. Resume preserves the existing global
epoch, model and optimizer state, dataset identity, and early-stopping counters.
For example, three more epochs after epoch 6 are displayed as:

```text
Epoch 7 (run 1/3)
Epoch 8 (run 2/3)
Epoch 9 (run 3/3)
```

Progress uses simultaneous `main completed/total` and `focus completed/total`
counters. `main` is the natural stream; `focus` is the modern-Go curriculum.
Fresh runs use **feature-balanced focused sampling**: each focused feature gets an
equal scheduling opportunity, and families are rotated within a feature before
individual windows are recycled. Corpus size therefore does not let a large
protobuf/struct-tag pool drown out smaller capabilities such as function-range.
The total focus budget is unchanged. Legacy checkpoints created before this
strategy retain their original window-uniform schedule when resumed.
Unlike a phase-dependent loss display, the live loss fields always refer to the
latest **main** batch, even when a progress line follows a focused update. Focus
loss is reported separately in the epoch summary. The explicit field names are
`loss`, `boundary_loss`, `type_loss`, and `modifier_loss`: these are optimization
losses, not F1 scores. Lower loss is better; it need not approach 0.99.

After each epoch, the console prints a multiline scorecard:

```text
Training losses (lower is better)
  train loss
  boundary loss
  token type loss
  modifier loss
  focus loss

Natural validation (higher F1 is better)
  boundary macro F1
  token type macro F1
  exact span F1
  exact span macro F1
  predicted/gold spans
  modifier F1 (Gold starts)

Focused validation (higher F1 is better)
  ...the same diagnostics, scored separately...

Timing
  train time
  validation time
  checkpoint time
  epoch time
  remaining in this run
  run ETA
```

Numbers in the scorecard come from the existing validation results. Boundary and
token-type diagnostics retain their existing masks. The displayed modifier F1 is
micro-averaged from the existing TP/FP/FN counts at Gold span beginnings, not a new
end-to-end quality claim. The natural/focus results are never pooled. **Best
checkpoint selection remains natural whole-document exact-span F1**, excluding
modifiers; logging changes do not switch selection to macro F1.

`win/s` is actual processed windows per second; training throughput includes
repeated focused presentations. A training progress line's `ETA` estimates the
remaining **training loop**, while a validation line has its own elapsed time and
ETA. The whole-run ETA appears after the first completed epoch, using measured
training + validation + checkpoint time. It is an estimate, not a deadline, and
may change with device load or early stopping. No five-hour estimate is hardcoded.
`epoch time` includes all three phases, unlike a training-only timer. Startup
checksum verification and class-frequency counting happen before the first epoch
and are not repeated on each epoch; the estimated remaining run excludes already
completed startup work. End-of-epoch JSON reports retain separate timing fields.

`GO_LOG_EVERY` defaults to 25 main batches (and 25 validation batches). The first
and final progress lines are always printed. This is a log interval, not a data
sampling limit. The update does not reduce the validation dataset, change losses,
or claim to speed up an individual full epoch. Short runs reduce waiting before
reviewing results; phase timings help identify actual bottlenecks.

For an already running older trainer, wait for a completed epoch and its `Saved:`
line before pressing Ctrl+C and applying an update. Resume from that run's
`last.pt`, not from `best.pt`, not from smoke weights, and not with `make train-go`
(which starts a fresh run). A few steps of an interrupted partial epoch may need
to be repeated; completed epochs and existing checkpoints are preserved.

## Checkpoints and interrupted runs

Default outputs are distinct timestamped directories:

```text
artifacts/go/
  smoke-<timestamp>/
  context512-<timestamp>/
    run.json
    best.pt
    last.pt
    epochs/
      epoch-0001.json
      ...
```

A smoke run additionally writes `smoke-report.json` and `smoke-prediction.json`.
These paths are already covered by the repository's `artifacts/` ignore rule.
Nothing is placed under `packs/go/model/` automatically and the Playground remains
on the selected TypeScript model. Neither the original corpora nor prepared
snapshots are changed or deleted.

Use `GO_RUN` to request an explicit empty run directory. A nonempty directory is
refused; rerunning training cannot silently overwrite an existing experiment.
Checkpoints and JSON reports are atomically replaced. A run-local lock prevents
concurrent training writes. After a hard kill, investigate the recorded process
before manually removing a stale lock; never delete old artifacts as a retry step.

`last.pt` stores the last **completed epoch**, including model and optimizer state,
loss weights, schema, snapshot/hash, sampling settings, epoch/early-stopping state,
and Python/CPU/accelerator RNG state. `best.pt` stores the checkpoint with the best
natural validation selection score. They are local experiments, not formal exports.
Only load checkpoints from trusted sources, even with `weights_only=True`.

Resume with the actual path printed by the completed run:

```bash
make continue-go GO_CHECKPOINT=artifacts/go/context512-RUN/last.pt GO_EPOCHS=3
```

`GO_EPOCHS` means **additional epochs** when resuming. The saved dataset path is
used instead of a potentially changed `current.json`; the snapshot can be relocated
with the Python CLI `--snapshot`, but its manifest hash and schema must still match.
Resume preserves model/sampling/optimizer configuration and early-stopping state.
It does not silently reset a smoke run into full training or accept a new dataset.
If an otherwise compatible checkpoint lacks optimizer state, a fresh AdamW optimizer
is announced explicitly. Normal trainer checkpoints always include it.

Interrupting an epoch preserves earlier complete checkpoints; the partial epoch
is not committed. An interruption before the first completed epoch leaves no
resumable `last.pt`. Changing hardware or PyTorch releases does not guarantee
bitwise replay even though RNG states are saved. CPU regression tests verify
same-environment uninterrupted training against completed-epoch resume.

## Evaluation without answer-key window boundaries

Every training epoch evaluates natural and focused validation documents separately.
Prepared validation windows were cut without Gold span boundaries. The evaluator
runs those fixed windows in batches, reassembles logits into each complete document,
and **only then** decodes and compares spans. A string crossing a window edge is
not counted as two artificial Gold spans. No validation source is used in backprop.

Reports include exact-span precision/recall/F1 for `(start, end, tokenType)`, per-role
scores, macro F1 over roles present in Gold or predictions, and separate exact-span
scores that also require matching modifier sets. They also include boundary/type
confusion matrices and modifier scores at Gold beginnings. Those Gold-conditioned
modifier diagnostics are not an end-to-end modifier correctness claim. Focused
feature scores retain the limitations of the small template-based curriculum.

Checkpoint selection uses **natural validation whole-document exact-span F1 under
fixed-window inference**, excluding modifiers. There is no pooled natural/focus
selection score. An explicit independent pass measures the actual predicted
adaptive runtime cursor, which can produce different results:

```bash
make evaluate-go GO_CHECKPOINT=artifacts/go/context512-RUN/best.pt
```

This defaults to validation and writes a new timestamped report. The sequential
adaptive pass may be slower than batched fixed-window evaluation. Once the model
and settings have been selected, run the held-out test once for the intended report:

```bash
make evaluate-go GO_CHECKPOINT=artifacts/go/context512-RUN/best.pt GO_EVAL_SPLIT=test
```

The trainer never invokes test evaluation. The evaluation CLI refuses test scoring
for a smoke checkpoint. Neither validation performance nor template coverage is
proof of generalization to arbitrary unseen Go projects.

## Source prediction

```bash
make predict-go GO_CHECKPOINT=artifacts/go/context512-RUN/best.pt GO_SOURCE=path/to/sample.go
```

Omitting `GO_SOURCE` reads UTF-8 source from standard input. The Python CLI also
supports `--output path/to/result.json`. Input bytes are read without CRLF conversion.
The output is a plain, theme-independent public `HighlightResult` with UTF-16 offsets,
ordered non-overlapping spans, token types, and optional modifiers. Raw checkpoint
or dataset metadata is not mixed into that public result.

Inference uses the neural boundary head to choose adaptive cuts, with one complete
lookahead character. It uses no Gold, Go AST, compiler, framework parser, or type
checker. Oversized spans still make progress; UTF-8 code points are not split.
Decoding is greedy, with type scores averaged over character starts and modifiers
read at predicted span beginnings. Struct tags can remain whole `string` spans;
this step does not add framework-specific public token types or styling.

The Python CLI is a development inference entry point. Browser export, a formal Go
SemanticPack runtime adapter, and Playground integration are separate future work.

## Verification scope

`make check` includes CPU-only trainer regressions alongside the existing data
checks. The new tests exercise masks/loss gradients, stream scheduling, snapshot
checksums, independent encoder initialization, whole-document validation across
window edges, Unicode/CRLF, adaptive cursor progress, checkpoint reload, completed-
epoch resume, and test-split isolation. Small synthetic fixtures used by these tests
are engineering checks and are not appended to real model corpora.

## PyTorch references

- [Saving and loading model and optimizer state](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)
- [Transformer encoder initialization guidance](https://docs.pytorch.org/docs/stable/generated/torch.nn.TransformerEncoder.html)
- [MPS backend](https://docs.pytorch.org/docs/stable/notes/mps.html)
- [Checkpoint serialization](https://docs.pytorch.org/docs/stable/notes/serialization.html)
- [Reproducibility limitations](https://docs.pytorch.org/docs/stable/notes/randomness.html)

## V3 final-training candidate

The V3 candidate removes feature-specific patch scheduling from the active final
workflow. Historical runs remain reproducible, but final training selects the
`modern-v3` and `real-world-v3` focused corpora and always trains the full V3
capability set together.

The final schedule uses one focused batch per four natural batches with
feature-balanced sampling. Natural windows still receive one complete presentation
per epoch. The larger focused budget is fixed before final training; it is not
changed in response to individual validation failures.

V3 model selection can use `--selection-policy quality-gated`. Under that policy an
epoch is eligible for `best.pt` only after all of the following hold on validation:

- natural exact-span F1 >= 0.95;
- natural exact-span macro F1 >= 0.90;
- focused exact-span F1 >= 0.98;
- every natural token role with support >= 32 has F1 >= 0.90;
- every V3 targeted capability has support >= 32 and F1 >= 0.90.

The V3 targeted capabilities are:

- `self-reference / interface`;
- `function-range / method`;
- `generic-method / method`;
- `generic-alias / type-parameter`;
- `struct-tags / string`;
- `strings / string`.

Among eligible epochs, `best.pt` is still selected by natural exact-span F1. Early
stopping does not begin counting patience before the first quality-eligible epoch,
so a from-scratch run cannot stop merely because aggregate natural F1 plateaued
before the semantic gates were learned.

Use `make train-go-v3-check` only for short curriculum verification with
weights-only initialization. Use `make train-go-final` only after the V3 dataset,
model, loss, sampler, and validation gates are frozen. `train-go-final` refuses a
previous initialization checkpoint and feature-specific focus filters, so it starts
from random initialization rather than inheriting the diagnostic patch history.

## Focused Curriculum V2 transfer runs

A V2 prepared snapshot intentionally has a different dataset identity from the V1
baseline. Do not use `--resume` across snapshots. Preserve the V1 `best.pt` and use
weights-only initialization instead:

```bash
make train-go-v2 \
  GO_INIT_CHECKPOINT=artifacts/go/context512-RUN/best.pt \
  GO_EPOCHS=1
```

This loads only model weights. AdamW state, RNG state, early-stopping counters,
loss weights, and checkpoint selection state are rebuilt for the new snapshot. The
new run records its source checkpoint hash and epoch in `run.json`. The V1 run is
never overwritten.

Every validation report now prints a targeted role scoreboard. The current
acceptance-oriented gate is F1 >= 0.90 for:

- `self-reference / interface`
- `function-range / method`
- `generic-method / method`
- `generic-alias / type-parameter`
- `struct-tags / string`

The scoreboard is diagnostic and does not silently change best-checkpoint selection,
which remains natural exact-span F1. A V2 experiment is useful only when the weak
roles improve while natural-code metrics remain stable.
