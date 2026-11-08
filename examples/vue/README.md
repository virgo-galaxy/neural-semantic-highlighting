# Vue 3 integration

Use an existing Vue 3 + TypeScript frontend with an ESM bundler (Vite is verified).
Install the same local npm archives as for React or vanilla JS.

1. Copy [the shared initializer](../highlighter.ts) to `src/highlighter.ts`.
2. Copy [CodeBlock.vue](CodeBlock.vue) to `src/components/CodeBlock.vue`.
3. Use it from `src/App.vue`:

```vue
<script setup lang="ts">
import CodeBlock from "./components/CodeBlock.vue";
const source = "const answer = 42;";
</script>

<template>
  <CodeBlock :code="source" language="typescript" />
</template>
```

The full component is also printed in the root README. Mounting starts inference
on the client; a watcher handles source/language changes, loading/errors and
obsolete results. Unmounting stops the watcher and updates. Multiple blocks share
one worker through the initializer, just like the React example. Close that
shared highlighter only when the entire application is disposed.

`v-html` receives NSH's escaped token markup. Ordinary Vue text interpolation
keeps code visible and escaped while loading or after an error.

For light/dark switching, per-block overrides and customization, follow the
[root theme guide](../../README.md#light--dark-themes-and-custom-css). Copy
[theme.css](../theme.css) to `src/theme.css` and import it after the default theme
in the initializer. Use a global stylesheet; scoped selectors do not automatically
reach token elements inserted with `v-html`. `:deep()` is an option for those
selectors, and CSS variables on the component's own `.nsh` element inherit normally.
