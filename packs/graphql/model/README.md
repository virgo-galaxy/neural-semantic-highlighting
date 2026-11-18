# GraphQL neural model

One standalone model highlights executable operations and SDL source. First
independent natural exact-span F1 is **96.36% on 14 documents**.

```ts
const { html } = await highlighter.highlight(source, { language: "graphql" });
```

`graphql` and `gql` (case normalized) share canonical `graphql` output and one
model asset; `.graphql` and `.gql` are accepted source suffixes. Use explicit
language selection. Selective import: `@nsh/highlighter/languages/graphql`.
Existing Markdown composition can reuse a registered `graphql`/`gql` fence.
The browser and Playground need no Python, GraphQL server, schema or parser.

See [evaluation](BENCHMARKS.md), [limits](KNOWN_ISSUES.md) and
[semantics](../SEMANTICS.md). Training resumes full artifacts checkpoints only.
All older weights/data/experiments are preserved; distribution remains private.
