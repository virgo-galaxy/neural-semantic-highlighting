# Markdown training

The model has 894,227 parameters. Use the established four-layer, width-128, four-head, FFN-512 Transformer with
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

For the November 17 optimization, retain the v1 checkpoint and run matched short
real-source experiments before calibration. The optional local-byte residual did
not improve the matched three-epoch control and was not selected. The selected
backbone remains unchanged. The added multiline fence curriculum follows actual
validation/display review; no independent test predictions guide refinement.

The optional joint BIO/role decoder fits legal transition probabilities from
natural **training** Gold and selects emission/transition weights on natural
**validation** only. It consumes neural logits, with no source-language parser,
regular expression or source-spelling rules. Existing packs without calibrated
parameters keep their historical greedy decoder. Calibration writes a separate
full checkpoint, preserving the original weights, optimizer and RNG state.
Any later optimizer update clears calibration and requires a new fit.

    .venv/bin/python -m training.markdown.calibrate --checkpoint artifacts/markdown/RUN/candidates/SELECTED.pt --output artifacts/markdown/RUN/calibrated.pt --device mps
    .venv/bin/python -m training.markdown.review --checkpoint artifacts/markdown/RUN/calibrated.pt --output artifacts/markdown/RUN/review.json --device mps
    .venv/bin/python -m training.markdown.challenge --checkpoint artifacts/markdown/RUN/calibrated.pt --output artifacts/markdown/RUN/golden.json --device mps

Freeze the candidate and stop training before the final test. Report the 20 new
independent natural documents separately from the 14 exposed v1 regressions:

    .venv/bin/python -m training.markdown.evaluate --checkpoint artifacts/markdown/RUN/calibrated.pt --split test --cohort-groups packs/markdown/dataset/optimization-cohorts.json --output artifacts/markdown/RUN/test.json --device mps

The test report binds the exact calibrated decoder as well as the checkpoint,
snapshot and semantic contract. Browser and Python inference use the same joint
state path and original UTF-16 offsets. Export and full-document parity follow
the existing native/browser/independent-consumer workflow.
