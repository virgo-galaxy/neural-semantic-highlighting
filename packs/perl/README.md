# Perl pack

One Perl 5 entry uses the existing small byte Transformer, local Python process,
UTF-16 span protocol, renderer and themes. Offline Gold reads source with the
already available PPI parser; source is never compiled or executed. No additional
Perl environment is installed. Read [SEMANTICS.md](SEMANTICS.md) for role limits.

Original source/Gold/prepared snapshots stay external under
`~/Datasets/neural-semantic-highlighting/perl`; resumable full checkpoints stay
under `artifacts/perl`. Selected `model/model.pt` is inference-only, never a
resume checkpoint. Preserve existing models, datasets and historical experiments.
The repository remains private. Golden/Playground are excluded from collection.

The [selected model](model/README.md) and five Playground examples are available.
First natural/focus exact-span test F1 is 83.60%/88.21%. Consecutive mixed Here
Documents and role/modifier boundaries remain explicit measured limits.
