# Vue training

Same small-model family: 4 Transformer layers, width 128, 4 heads, FFN 512,
512 UTF-8 bytes, 894,485 parameters, 17 base markup/region roles and one closing
modifier. Reuse source-agnostic Transformer, adaptive inference, UTF-16 decoding,
loss and atomic-file code from the HTML implementation. Vue owns schemas, data,
weights, training state and artifacts. Provenance binds shared and Vue code hashes.

```bash
make train-vue-smoke
make train-vue VUE_INIT_FROM=artifacts/html/<run>/best.pt VUE_EPOCHS=3
make continue-vue VUE_CHECKPOINT=artifacts/vue/<run>/last.pt VUE_EPOCHS=3
make evaluate-vue VUE_CHECKPOINT=artifacts/vue/<run>/best.pt
make evaluate-vue-composed VUE_CHECKPOINT=artifacts/vue/<run>/best.pt
make challenge-vue VUE_CHECKPOINT=artifacts/vue/<run>/best.pt
```

Weights-only initialization accepts a compatible full training checkpoint, with
backbone/BIO and semantic head rows copied by name. New Vue region roles start
fresh; optimizer, RNG and selection state are fresh. Never use an inference-only
artifact. Resume the same run's `last.pt` with the same frozen data/configuration,
restoring optimizer and RNG. Locks prevent concurrent writers.

Defaults: three additional epochs, batch 32, AdamW 0.0003, decay 0.01, clip 1.0,
modifier loss 0.1 / threshold 0.60, seed 42, patience five. Each natural window is
presented once per epoch; bounded focus batches of 16 rotate after natural batches.
Class weights count unique labels. Padding/UTF-8 continuation bytes are ignored;
modifiers are supervised at span starts only. Short smoke tests verify state and
inference, not quality. Use `caffeinate -i` and durable logs for observed local runs.

Selection averages natural validation exact-span macro F1 across Vue 2, Vue 3 and
Vue 3.2 profiles. Every profile must have real-source evidence. Report natural and
focus streams, profile and feature metrics, exact regions and typed character
coverage separately. Fixed-window validation reassembles complete documents before
decoding, without Gold cuts; independent evaluation uses actual predicted cuts.

Composed evaluation invokes the existing JS/TS/JSX/TSX and CSS/SCSS/Less neural
packs in predicted Vue regions. Mustache interiors use a fixed expression wrapper,
then project original source positions. Offline reference Gold is independent;
unsupported child syntax is explicitly excluded with counts/profile/source IDs.
No Gold region, runtime parser or source regex selects child inference. Attribute
values remain whole strings in this initial contract. Reserve test for one frozen
reviewed candidate; document child-model and template-boundary limits.
