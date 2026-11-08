# React integration

Use an existing React + TypeScript frontend with an ESM bundler (Vite is verified).
Install the local npm archives as described in the root README.

1. Copy [the shared initializer](../highlighter.ts) to `src/highlighter.ts`.
2. Copy [CodeBlock.tsx](CodeBlock.tsx) to `src/components/CodeBlock.tsx`.
3. Use it from `src/App.tsx`:

```tsx
import { CodeBlock } from "./components/CodeBlock";

export default function App() {
  return <CodeBlock code={"const answer = 42;"} language="typescript" />;
}
```

The complete source is also included in the root README. The component handles
changing props, plain-code loading/error fallback and obsolete results. The HTML
passed to `dangerouslySetInnerHTML` is escaped by NSH. Effects start only on the
client; for Next.js App Router add `"use client"` to `CodeBlock.tsx`.

Multiple code blocks share one highlighter. Component cleanup stops updates;
close the shared instance only when the entire application is disposed. Closing
it whenever one block unmounts would interrupt other blocks.

For themes and custom global CSS, follow the
[root theme guide](../../README.md#light--dark-themes-and-custom-css). Copy
[theme.css](../theme.css) to `src/theme.css` and import `"./theme.css"` after the
default theme in `src/highlighter.ts` to try the example palette and layout.
