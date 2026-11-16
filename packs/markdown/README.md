# Markdown pack

Markdown/GFM source highlighting with headings, emphasis, links, lists, task
checkboxes, tables, code, comments and original Unicode/line endings. Predicted
top-level fenced bodies can reuse explicitly registered language models; unknown
languages remain code. Frontend consumers need no Python or Markdown parser.

See [semantics](SEMANTICS.md), [dataset](dataset/README.md),
[Golden](fixtures/README.md), [training](../../training/markdown/README.md)
and [consumer integration](../../README.md).

The optimized model reaches 95.10% exact-span F1 on 20 new independent real
documents; the original 14-file regression improves from 77.24% to 95.99%.
See [evaluation](model/BENCHMARKS.md) for separate cohorts and remaining limits.
The complete [v1 native](model-20261116-v1/README.md) and
[v1 browser](browser-20261116-v1/model.json) bundles remain preserved.
