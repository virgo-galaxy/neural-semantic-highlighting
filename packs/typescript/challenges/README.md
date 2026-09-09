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

## Paired contextual RegExp diagnostic

`regexp-paired-context.json` isolates one additional question: does the exact
same RegExp literal behave differently when it appears in a tiny isolated
snippet versus a realistic TypeScript context?

Each pair uses one identical RegExp literal twice:

- `isolated`: a tiny source file with heavy padding at inference time.
- `contextual`: a 160–480 byte TypeScript source with normal surrounding code.

The paired evaluator reports exact RegExp span F1 for both sides plus four
transitions: `both_exact`, `contextual_only`, `isolated_only`, and
`neither_exact`.

Validate the paired challenge definition with:

```bash
make validate-regexp-paired-challenge-typescript
```

Run it against the frozen V3 Epoch 19 model and the 300/400-step RegExp surgery
snapshots with:

```bash
make challenge-regexp-paired-typescript
```

Like `regexp.json`, this paired challenge is evaluation-only and must never be
merged into train, validation, or test data.
