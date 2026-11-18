# Protocol Buffers neural model

One standalone model highlights `.proto` messages, enums, services/RPCs,
packages/imports, maps/oneofs, reserved fields, options and original strings/comments.
First independent natural exact-span F1 is **98.55% on 12 documents**.

```ts
const { html } = await highlighter.highlight(source, { language: "proto" });
```

`protobuf`, `proto` and `protocol-buffers` (case normalized) share canonical
`protobuf` output. Source suffix is `.proto`. Selective import:
`@nsh/highlighter/languages/protobuf`; `languages/proto` re-exports the same model.
Only one ONNX asset is emitted. Existing Markdown composition can reuse a
registered `proto`/`protobuf` fence. Source is explicit, not automatically detected.
No protoc, SDK, Python, imported schemas, code generator or server is needed.

See [evaluation](BENCHMARKS.md), [limits](KNOWN_ISSUES.md) and
[semantics](../SEMANTICS.md). Use only full artifacts checkpoints for training.
All older weights/data/experiments are preserved; distribution remains private.
