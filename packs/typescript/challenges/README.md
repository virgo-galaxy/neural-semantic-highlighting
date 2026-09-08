# TypeScript RegExp Challenge

This directory contains standalone evaluation material for RegExp literal recognition.

`regexp.json` is **not** part of the training, validation, or test split. It is a challenge set used to answer one focused question: can the neural runtime distinguish JavaScript/TypeScript RegExp literals from slash-shaped non-RegExp syntax such as division, `/=`, strings, comments, and JSX closing tags?

The `⟦...⟧` markers in positive cases define exact expected RegExp spans. The evaluator removes the markers before inference, so the model never sees them.

The initial set contains 160 cases: 100 positive cases, 60 negative cases, and 105 exact RegExp spans. It covers basic literals, flags, escapes, character classes, groups/assertions, TypeScript/TSX contexts, division, strings/templates, comments, and JSX slash syntax.

Run validation of the challenge definition with:

```bash
make validate-regexp-challenge-typescript
```

Run the challenge against the frozen V2 Epoch 20 checkpoint with:

```bash
make challenge-regexp-typescript
```

Do not merge these cases into any training corpus. If the challenge exposes a systematic weakness, create new training-only hard cases that express the same pattern without copying the challenge cases.
