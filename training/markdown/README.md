# Markdown training

Use the established four-layer, width-128, four-head, FFN-512 Transformer with
512 original UTF-8 bytes of context and the pack's prose/code-role schema.
Initialize compatible weights from the full reviewed XML artifacts checkpoint;
new role/modifier heads are fresh. Existing Node and pinned Prettier parse-only
assets provide offline AST positions; no SDK/global package installation occurs.

    make dataset-markdown
    make test-labeling-markdown
    caffeinate -i make train-markdown-smoke MARKDOWN_DEVICE=mps MARKDOWN_RUN=artifacts/markdown/smoke MARKDOWN_INIT_FROM=artifacts/xml/context512-refine-20261116-01/candidates/epoch-0003.pt
    caffeinate -i make train-markdown MARKDOWN_DEVICE=mps MARKDOWN_EPOCHS=3 MARKDOWN_RUN=artifacts/markdown/context512 MARKDOWN_INIT_FROM=artifacts/xml/context512-refine-20261116-01/candidates/epoch-0003.pt
    caffeinate -i make continue-markdown MARKDOWN_DEVICE=mps MARKDOWN_EPOCHS=3 MARKDOWN_CHECKPOINT=artifacts/markdown/context512/last.pt

External immutable data stays under ~/Datasets/neural-semantic-highlighting/markdown;
full optimizer/RNG checkpoints, invocations and timings stay under artifacts/markdown.
Archive candidates before continuation. Review actual natural validation,
independent Golden and displays before freeze; then run the first adaptive test
and stop training. Keep base-role, predicted fence routing and composed/native
consistency evidence separate. Never resume packs/*/model/model.pt or ONNX.
Preserve historical data/experiments and all old formal models. Frontend inference
uses the existing browser Worker with no offline parser, Python bridge or runtime
source-parser/regex repair.
