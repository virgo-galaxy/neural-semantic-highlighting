# Vue 3 integration

Use an existing Vue 3 + TypeScript app with Vite. Follow the
[archive installation guide](../../docs/model-delivery.md#install-from-local-archives)
for your chosen model source.

1. Copy one initializer to `src/highlighter.ts`.
   - **Website assets:** use [highlighter.ts](../highlighter.ts) and install `@nsh/models`.
   - **Remote host:** use [highlighter-remote.ts](../highlighter-remote.ts). Set
     `modelBaseUrl` to your [deployed model directory](../../docs/model-delivery.md#remote-assets-static-server-or-minio).
2. Copy [CodeBlock.vue](CodeBlock.vue) to `src/components/CodeBlock.vue`.
3. Use the component in `src/App.vue`. The same code works with either initializer:

```vue
<script setup lang="ts">
import CodeBlock from "./components/CodeBlock.vue";
const source = "const App = () => <button>Hello</button>;";
const styles = ".card { &:hover { color: red; } }";
</script>

<template>
  <CodeBlock :code="source" language="tsx" />
  <CodeBlock :code="styles" language="scss" />
</template>
```

Mounting starts inference on the client. A watcher handles source/language changes, loading/errors and
obsolete results. Unmounting stops the watcher and updates. Multiple blocks share
one worker through the initializer, just like the React example. Close that
shared highlighter only when the entire application is disposed.

`v-html` receives NSH's escaped token markup. Ordinary Vue text interpolation
keeps code visible and escaped while loading or after an error.

Run the app's normal `npm run dev` and `npm run build` commands. For the local
initializer, the Vite build contains the TypeScript and CSS ONNX files. For the
remote initializer, deploy the model directory separately so the app ships zero
ONNX files. Both builds include the shared browser runtime. The example app is
written in Vue and highlights TSX/SCSS. To highlight `.vue` source itself,
register the `vue` descriptor locally or include `"vue"` in the remote selection
and export the matching model resources.

For light/dark switching, per-block overrides and customization, follow the
[root theme guide](../../README.md#light--dark-themes-and-custom-css). Copy
[theme.css](../theme.css) to `src/theme.css` and import it after the default theme
in the initializer. Use a global stylesheet; scoped selectors do not automatically
reach token elements inserted with `v-html`. `:deep()` is an option for those
selectors, and CSS variables on the component's own `.nsh` element inherit normally.
