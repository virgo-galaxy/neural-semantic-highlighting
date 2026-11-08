# Assembly pack

One independent neural Assembly entry covers common NASM/Intel, GNU/AT&T,
MASM and AArch64 source. It reuses the established small byte Transformer,
external dataset, Gold/Golden, full-checkpoint training, UTF-16 spans, local bridge,
HTML renderer and themes. [SEMANTICS.md](SEMANTICS.md) defines exact display scope.

No x86/Windows environment, assembler or emulator is installed. Original source
is never compiled, linked, macro-expanded or executed, including during offline
Gold construction. Inference uses only neural weights and the original text.

Immutable source/Gold/prepared revisions stay under
`~/Datasets/neural-semantic-highlighting/assembly`; full resumable checkpoints stay
under `artifacts/assembly`. Selected `model/model.pt` is inference-only; never use
it to resume training. Golden and Playground remain outside collection. Preserve
all previous data/models/experiments and keep the repository private.
