# Zig pack

Current **Zig 0.17.1 only**, original `.zig` source. Official SDK syntax, comptime,
containers, errors/optionals, captures, builtin calls and local semantic roles.
Historical Zig APIs/syntax and master snapshots are not coverage targets.

See [contract](SEMANTICS.md), [dataset](dataset/README.md),
[Golden](fixtures/README.md) and [training](../../training/zig/README.md).
Frontend inference requires no Zig compiler, SDK, parser or highlighting server.

The selected [model](model/README.md) is available through `language: "zig"` and
`@nsh/highlighter/languages/zig`. [Evaluation](model/BENCHMARKS.md) records
92.51% natural test exact-span F1 over 21 files and separates visible examples.
[Known issues](model/KNOWN_ISSUES.md) retain quoted-identifier, literal-boundary
and local-name limitations. Full resumable checkpoints stay in `artifacts/zig`.
