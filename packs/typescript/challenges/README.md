# TypeScript RegExp Challenges

This directory contains evaluation-only material for RegExp literal recognition. Challenge cases are never part of train, validation, or test data.

`regexp.json` asks one focused question: can the neural runtime distinguish JavaScript/TypeScript RegExp literals from slash-shaped non-RegExp syntax such as division, `/=`, strings, comments, and JSX closing tags?

The `⟦...⟧` markers in positive cases define exact expected RegExp spans. Evaluators remove the markers before inference, so the model never sees them.

Validate the challenge definition with:

```bash
make validate-regexp-challenge-typescript
```

Run it against the current checkpoint with:

```bash
make challenge-regexp-typescript
```

If the challenge exposes a systematic weakness, create new training-only examples that express the same pattern without copying challenge cases.

## Paired contextual RegExp diagnostic

`regexp-paired-context.json` checks whether the exact same RegExp literal behaves differently in a tiny isolated snippet versus realistic TypeScript context.

Each pair contains:

- `isolated`: a tiny source containing the target literal.
- `contextual`: the same literal inside ordinary surrounding TypeScript code.

The paired evaluator reports exact RegExp span F1 for both sides plus four transitions: `both_exact`, `contextual_only`, `isolated_only`, and `neither_exact`.

Validate it with:

```bash
make validate-regexp-paired-challenge-typescript
```

Run it against the current checkpoint with:

```bash
make challenge-regexp-paired-typescript
```

The paired challenge is also evaluation-only and must never be merged into training data.
