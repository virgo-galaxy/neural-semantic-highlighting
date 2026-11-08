# AWK neural model

One 893,582-parameter byte Transformer covers common POSIX-style and GNU AWK
source through one AWK entry. Inference returns original UTF-16 semantic spans
without AWK execution, a lexer, includes, extension loading or source-regex repair.

The selected full checkpoint is frozen epoch 15:
`artifacts/awk/context512-20261108-01/candidates/epoch-0015.pt`.
A 3-epoch measured transfer from the full Perl checkpoint was followed by 12 short
continuation epochs. The architecture and workflow remain unchanged; no inference
export was used for training. Full resumable checkpoints stay in `artifacts/awk`.

The first natural/focused test measured 96.89%/99.87% exact-span F1. These are
small source-family holdouts, not universal AWK accuracy. Common fields, arrays,
functions, phases and regex work in the displayed examples; advanced GNU call
roles and regex boundaries remain in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

```sh
.venv/bin/python -m packs.awk.runtime.local --file example.awk
```

This float32 export is inference-only. Source, Gold and immutable prepared data
stay external under `~/Datasets/neural-semantic-highlighting/awk`. Offline Gold
uses pinned isolated lexer assets and a bounded role adapter; no AWK environment
was installed and source is never executed. Preserve all prior models, datasets
and experiments. Repository remains private. Playground uses the same persistent
local bridge; `NSH_AWK_CHECKPOINT` selects a compatible development checkpoint.
