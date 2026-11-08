# React code block

Copy `CodeBlock.tsx` into a React frontend and import it:

```tsx
<CodeBlock code={source} language="tsx" />
```

Before publication, build the local archives with `pnpm pack:browser` in the NSH
checkout. In the consuming app, install all four archives together:

```bash
npm install /path/to/neural-semantic-highlighting/artifacts/browser/npm/*.tgz
```

The component uses one shared highlighter. It displays ordinary escaped React
text while a result is loading, ignores results for older props, and shows an
error if inference fails. Returned markup is escaped by the NSH renderer before
it reaches `dangerouslySetInnerHTML`. No code is executed or sent to a server.

The shared instance is intentionally kept for the app lifetime. If your app owns
the highlighter explicitly, close it when the app is disposed. Do not close a
shared instance every time one of several code blocks unmounts. For Next.js, put
this component behind a client boundary (`"use client"`).

An independent React/Vite production app using local tarballs was verified; see
[the runtime report](../../docs/browser-runtime.md). npm publication is pending.
