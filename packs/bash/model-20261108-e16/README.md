# Shell neural model

One 893,582-parameter, four-layer byte Transformer covers POSIX sh, Bash, Zsh and
Csh/Tcsh through one Shell entry. Git Bash uses the same Bash syntax. Profiles
describe offline coverage, not interchangeable execution environments or separate
runtime parsers. Source enters the existing local neural process and returns
UTF-16 semantic spans. No shell, Pygments, compiler, command lookup or script
execution participates in inference.

The selected candidate is frozen epoch 16 from
`artifacts/bash/context512-coverage-20261108-01/candidates/epoch-0016.pt`.
The run completed 20 epochs. It transfers full training checkpoints from the
preserved Shell experiments, originally initialized from the full Go epoch-29
checkpoint. No inference-only bundle was used for training.

The decoder follows the pack's canonical adjacent-string and modifier-role rules,
using predicted roles/ranges only. Checkpoint provenance binds the exact
`pack.json` hash; older experiments with a different policy/teacher must be
replayed with their matching code/configuration instead of silently relabeled.

The first independent natural test measured 84.20% exact-span F1 overall: Bash
93.28%, POSIX 89.33%, Csh 87.43%, Zsh 71.55%. Coverage is small and complex Zsh
files remain a material weakness. Original focused grammar is substantially
stronger, but is not a substitute for those natural results. Read
[BENCHMARKS.md](BENCHMARKS.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

```sh
.venv/bin/python -m packs.bash.runtime.local --file example.sh
```

The selected artifact contains float32 inference weights, not optimizer/RNG or
resume state. Full checkpoints remain under ignored `artifacts/bash`; source,
Gold and immutable snapshots remain external under
`~/Datasets/neural-semantic-highlighting/bash`. The repository stays private.
The Playground uses the same persistent local-process bridge as existing packs;
`NSH_BASH_CHECKPOINT` can select a configuration-compatible development candidate.
