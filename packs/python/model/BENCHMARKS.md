# Python baseline evaluation

Exact spans require UTF-16 start, end and role to match. Modifier-aware F1 also
requires the complete modifier set. Macro F1 includes every role with Gold or
predicted support. Natural source and original focused grammar are reported
separately. Low or zero support is not evidence of broad language accuracy.

| Adaptive MPS evaluation | Documents | Exact-span F1 | Role macro F1 | Including modifiers |
| ----------------------- | --------: | ------------: | ------------: | ------------------: |
| Natural validation      |         4 |        92.04% |        87.11% |      See raw report |
| Natural test            |         4 |        87.52% |        78.05% |              85.90% |
| Focus test              |        92 |        92.66% |        85.35% |              88.92% |

These are small, source-family-held-out estimates. The four test modules are not
four independent projects. They do not prove equivalent quality across all
Python libraries or versions. Natural test contains 5,119 Gold spans; common
keyword, operator, punctuation, method and property F1 are above 93%, while name
role distinctions are substantially weaker. Read the complete per-role report.

The first corpus freezes 40 CPython 3.15.0 standard-library modules, with PSF license
and original byte hashes retained. Original grammar adds 378 examples and the
short-fragment revision adds 576. Gold uses separately pinned CPython 3.15.0;
training/inference retains Python 3.12.2 and the existing PyTorch environment.
Source is parsed/tokenized offline, never imported or executed.

Exact, lexical and normalized-shape copies crossing source families are excluded.
All 994 documents receive valid Gold; 32 cross-family copies are excluded. The
remaining 962 split before windows, preserving the first frozen family map:

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| Train      |           32 |        690 |   1,456 |
| Validation |            4 |         92 |     180 |
| Test       |            4 |         92 |     179 |

Training visits every natural window and rotates bounded focus batches. Class
weights count unique train labels. Padding and UTF-8 continuation bytes are
ignored; modifiers are supervised only at span beginnings. Training cuts can use
Gold; validation uses fixed character-safe windows and whole-document reassembly.
Reported adaptive evaluation uses the actual predicted cursor with no parser,
Gold boundaries, overlap fusion or source-specific runtime correction.

Experiments: one smoke check, an initial 3+24-epoch transfer experiment, then a
12-epoch fragment experiment. Epochs take roughly 9–14 seconds on this host.
Selected fragment epoch 7 had natural fixed validation macro F1 0.8526 and was
frozen after real-source/Golden inspection. The completed run's later fixed-score
maximum was epoch 12; it is retained as an experiment, not substituted after
testing. The first independent adaptive test of epoch 7 took about 1.20 seconds
inside the evaluator; this is not a steady-state latency benchmark.

Ten independently marked Golden probes remain visible development evidence,
excluded from corpus collection. Only two are entirely exact including modifiers.
Most remaining cases have one or two mismatched spans/modifier sets, including
harmless whitespace-edge differences and real role errors; do not call these
probes perfect. Raw differences are preserved in `reports/golden-probes.json`.

Reproduce against the frozen source checkpoint and its external snapshot:

```sh
make evaluate-python PYTHON_CHECKPOINT=artifacts/python/context512-fragments-20261108-01/candidates/epoch-0007.pt
make challenge-python PYTHON_CHECKPOINT=artifacts/python/context512-fragments-20261108-01/candidates/epoch-0007.pt
```

The archived test is the candidate's first independent evaluation. Do not tune
against it and describe subsequent measurements on those same files as unseen.
Full checkpoint, snapshot and code identities are archived with the bundle.
