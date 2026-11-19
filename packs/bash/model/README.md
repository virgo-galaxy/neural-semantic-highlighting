# Shell neural model

One 894,366-parameter, four-layer byte Transformer covers
POSIX sh, Bash, Zsh and Csh/Tcsh through one Shell entry. Git Bash shares Bash
syntax. `.sh` filenames and shell aliases resolve through the same descriptor.

```ts
const { html } = await highlighter.highlight(source, { language: "bash" });
```

Browser/Playground inference uses the selected ONNX model in a Worker, without
Python, a shell SDK, command execution, lexer fallback or source-spelling repair.
`function` forms and Here Documents remain represented. Bash is prioritized:
its natural result is **94.29%**. The exposed 11-file legacy overall result is
**87.12%**; 12 additional Zsh functions reach **90.91%** separately. These are
bounded different cohorts, and complex dialects remain weaker.

All 19 strict Golden pass/fail outcomes match the preceding model (eight entirely
exact, including modifiers). Here Document terminators can still overrun into
following commands. The original focused 96.76% Here Document result belongs to
[the preceding archived selection](../model-20261119-v1/BENCHMARKS.md); it is not
claimed as a new measurement of this revision.

Current full checkpoint, window selection, corpus/profile and Golden details are
recorded in [BENCHMARKS.md](BENCHMARKS.md), `model.json` and
[KNOWN_ISSUES.md](KNOWN_ISSUES.md). Context remains 512 original UTF-8 bytes;
selected overlapping windows add inference work for long documents. Input text
and original UTF-16 offsets are preserved.

Optional native development/reference output:

```sh
.venv/bin/python -m packs.bash.runtime.local --file example.sh
```

The float32 inference artifact excludes optimizer/RNG state. Resume complete
`artifacts/bash` experiments only. External immutable source, Gold and prepared
snapshots remain under `~/Datasets/neural-semantic-highlighting/bash`. All old
experiments and formal bundles remain intact; the repository stays private.
