<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch, type WatchStopHandle } from "vue";

import { highlighter } from "../highlighter";

const props = defineProps<{ code: string; language: string }>();
const markup = ref<string>();
const error = ref("");
let stopWatching: WatchStopHandle | undefined;

// Start inference on the client, after hydration.
onMounted(() => {
  stopWatching = watch(
    () => [props.code, props.language] as const,
    ([code, language], _, onCleanup) => {
      let active = true;
      onCleanup(() => {
        active = false;
      });
      markup.value = undefined;
      error.value = "";
      highlighter.highlight(code, { language }).then(
        ({ value }) => {
          if (active) markup.value = value;
        },
        (reason: unknown) => {
          if (active) error.value = String(reason);
        },
      );
    },
    { immediate: true },
  );
});
onBeforeUnmount(() => stopWatching?.());
</script>

<template>
  <pre
    class="nsh"
    :data-language="language"
    :aria-busy="markup === undefined && !error"
  ><code v-if="markup !== undefined" v-html="markup"></code><code v-else>{{ code }}</code></pre>
  <p v-if="error" role="alert">{{ error }}</p>
</template>
