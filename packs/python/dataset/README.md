# Python corpus and Gold

The first bounded corpus uses 40 selected real CPython 3.15.0 standard-library
modules (PSF license retained) and 378 original grammar examples. It does not
download a new project corpus or collect independently authored Golden/Playground.
`sources.json` declares roots; each stdlib module and original curriculum directory
is an intact source family before byte windows. All paths, byte hashes and license
text are frozen externally. Original grammar data has no public license grant.

Offline Gold uses the separate pinned CPython 3.15.0 interpreter. The PyTorch
environment remains Python 3.12.2. Parsing/tokenization never executes source.
Modern f/t-strings are whole spans; annotations and names use source-local roles.
Read `../SEMANTICS.md` for boundaries. Invalid input is quarantined with its hash.

```sh
make dataset-python
```

The default Gold interpreter is under ignored `artifacts/tools/python`; override
`PYTHON_GOLD` with an already available modern interpreter. The command does not
install or upgrade any system environment. Dataset snapshots remain under
`~/Datasets/neural-semantic-highlighting/python`, full checkpoints under
`artifacts/python`, and the selected inference-only bundle under `../model`.
Frozen `split-groups.json` prevents existing validation/test families moving into
training in later revisions. Do not regenerate that map after looking at scores.

The short-fragment revision adds 576 independently generated development examples
for ordinary imports, decorators, async/non-async functions, builtin shadowing,
operators, contextual keywords, adjacent strings and Unicode/CRLF. Layouts and
leading positions vary. The first revision remains intact; existing source-family
assignments are preserved and only new families are assigned before training.
