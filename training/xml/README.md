# XML / SVG training

The established four-layer, width-128, four-head, feed-forward-512 Transformer
uses a compact eight-role markup schema plus closing modifier and 512-byte
context. Initialize compatible layers/role heads from the full HTML training
checkpoint, not its exported inference model. Existing CPython Expat supplies
independent offline validation; no SDK or package installation is needed.

    make dataset-xml
    make test-labeling-xml
    caffeinate -i make train-xml-smoke XML_DEVICE=mps XML_RUN=artifacts/xml/smoke XML_INIT_FROM=artifacts/html/context512-fragments-20261108-01/best.pt
    caffeinate -i make train-xml XML_DEVICE=mps XML_EPOCHS=3 XML_RUN=artifacts/xml/context512 XML_INIT_FROM=artifacts/html/context512-fragments-20261108-01/best.pt
    caffeinate -i make continue-xml XML_DEVICE=mps XML_EPOCHS=3 XML_CHECKPOINT=artifacts/xml/context512/last.pt

Natural and focus sources, XML and SVG, and independent Golden/display evidence
stay distinct. Review original XML and SVG validation sources, preserve candidates,
freeze before the first adaptive test and stop at a useful bounded baseline.
Full optimizer/RNG checkpoints and timings stay under artifacts/xml; immutable
external snapshots stay under ~/Datasets/neural-semantic-highlighting/xml.
Never resume exported packs/*/model/model.pt or ONNX, overwrite an old experiment,
expand external entities, or execute captured source. Frontend inference remains
pure neural browser Worker inference without the teacher or a Python process.
