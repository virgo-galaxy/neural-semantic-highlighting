# Shell pack

One `bash` document kind / Shell entry covers POSIX sh, Bash, Zsh and Csh/Tcsh.
Internal profiles retain separate natural/focus evaluation, with one neural model
and no runtime dialect parser. Git Bash shares Bash syntax and needs no extra
language entry. Read [SEMANTICS.md](SEMANTICS.md) for the local role contract.

Offline Gold reads source with pinned, isolated lexer assets and a local
command-position adapter. It never executes scripts or installs a shell. Pure
neural inference reuses the existing Transformer, byte cursor, span protocol,
local-process bridge, renderer and themes. Compiler/lexer tooling stays offline.

Source, Gold and prepared snapshots live under
`~/Datasets/neural-semantic-highlighting/bash`; full resumable checkpoints live
under ignored `artifacts/bash`. Golden and Playground are outside collection.
Versioned upstream source/license captures and original grammar families split
before windows, and frozen source-family assignments persist across revisions.

Use the established preparation, short training, real-source inspection, frozen
test and reviewed export workflow. Selected `packs/bash/model/model.pt` is an
inference-only bundle, never a resume checkpoint. Preserve existing formal
models, data revisions and experiments. Repository stays private.

The [selected model](model/README.md) and four-profile Playground are available.
Its known natural test F1 is 84.78% overall (Bash 93.20%, POSIX 88.32%, Csh 89.29%,
Zsh 73.76%); small natural samples and complex-script limits remain explicit in the
[benchmark](model/BENCHMARKS.md) and [known issues](model/KNOWN_ISSUES.md).

The Here Document follow-up covers quoted delimiters, `<<-`, variable-first
bodies and both function-keyword forms. New held-out focused tasks improve from
58.84% to 96.76% exact-span F1. The previous formal model is preserved in
[model-20261108-e16](model-20261108-e16/README.md). Short-snippet terminator
overruns remain measured limits; inference still uses the same pure neural path.
