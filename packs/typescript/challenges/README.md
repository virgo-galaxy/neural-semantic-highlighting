# TypeScript Challenges

This directory contains evaluation-only challenge material for the TypeScript language family. Challenge cases must never be merged into train, validation, or test data.

## RegExp literal recognition

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

## JSX / TSX semantics

`jsx-tsx.json` checks JSX and TSX behavior across intrinsic elements, components, attributes, fragments, JSX text, expression boundaries, qualified component names, spread props, TypeScript generic syntax, generic JSX components, and realistic React-shaped code.

Assertions use `⟦tokenType|text⟧` markers. The evaluator removes all markers before inference. `tag` and `attribute` are the primary focus types and receive exact-span precision, recall, and F1 metrics. Additional assertions verify TSX generic type parameters and that plain JSX text remains outside semantic spans.

Validate the challenge definition with:

```bash
make validate-jsx-tsx-challenge-typescript
```

Run it against the current checkpoint with:

```bash
make challenge-jsx-tsx-typescript
```

The challenge intentionally tests JSX/TSX language semantics, not React-specific concepts such as hooks or Tailwind utility classes.
