# Ruby neural model

Common modern Ruby .rb/.rake/.gemspec and Gemfile/Rakefile syntax, classes/modules, blocks, patterns, Rails-style calls, heredocs and percent/regex literals.

```ts
const { html } = await highlighter.highlight(source, { language: "ruby" });
```

Aliases `rb`, `rake`, `gemspec`, `gemfile` and `rakefile` normalize to `ruby`.
Selective import: `@nsh/highlighter/languages/ruby`. Case-normalized IDs share one
model. Browser/Playground consumers require no language SDK, interpreter/compiler,
parser, dependency environment or Python process. Offline Gold uses Tree-sitter Ruby 0.23.1 at ad907a69 with runtime 0.25.10, compiled with existing Clang only in project cache.
Collected projects and dependencies never execute or typecheck.

[Evaluation](BENCHMARKS.md) separates natural, focus and visible evidence;
[known limits](KNOWN_ISSUES.md) retain measured errors and source-local scope.
Selected .pt/ONNX are inference-only. Resume full artifacts/ruby checkpoints only.
All previous data, experiments and formal models remain preserved.
