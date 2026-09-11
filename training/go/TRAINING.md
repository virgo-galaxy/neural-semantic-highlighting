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

## First complete baseline

After smoke verification:

```bash
make train-go
```

This creates a **new** run, not a continuation of smoke weights. The default budget
is up to 32 epochs, with early stopping after five epochs without improvement in
natural validation exact-span F1. Model parameters start from random initialization;
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
make train-go GO_EPOCHS=32 GO_BATCH_SIZE=32 GO_FOCUS_EVERY=8
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
make continue-go GO_CHECKPOINT=artifacts/go/context512-RUN/last.pt GO_EPOCHS=16
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
