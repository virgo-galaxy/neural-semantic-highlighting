# React integration

Use an existing React + TypeScript app with Vite and install the
[npm package](../../docs/model-delivery.md#install-from-npm).

1. Copy [highlighter-remote.ts](../highlighter-remote.ts) to
   `src/highlighter.ts`. Set `modelBaseUrl` to your
   [deployed model directory](../../docs/model-delivery.md#remote-assets-static-server-or-minio).
2. Copy [CodeBlock.tsx](CodeBlock.tsx) to `src/components/CodeBlock.tsx`.
3. Use the component in `src/App.tsx`.

```tsx
import { CodeBlock } from "./components/CodeBlock";

export default function App() {
  return (
    <>
      <CodeBlock code={"const App = () => <button>Hello</button>;"} language="tsx" />
      <CodeBlock code={".card { &:hover { color: red; } }"} language="scss" />
    </>
  );
}
```

The component handles changing props, plain-code loading/error fallback and
obsolete results. `dangerouslySetInnerHTML` receives the escaped token markup
returned by NSH. An effect calls inference on the client.

Multiple code blocks share one highlighter. Component cleanup stops updates;
close the shared instance when the entire application is disposed.

Run the app's normal `npm run dev` and `npm run build` commands. Serve the
TypeScript and CSS model files at the selected URL. The browser downloads them
as the code blocks need them.

For themes and custom global CSS, follow the
[root theme guide](../../README.md#light--dark-themes-and-custom-css). Copy
[theme.css](../theme.css) to `src/theme.css` and import `"./theme.css"` after the
default theme in `src/highlighter.ts` to try the example palette and layout.
