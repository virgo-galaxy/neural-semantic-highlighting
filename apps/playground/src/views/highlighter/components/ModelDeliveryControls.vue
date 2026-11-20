<script setup lang="ts">
import { ref, watch } from "vue";

import AppIcon from "@/components/AppIcon.vue";
import type { PlaygroundModelSource } from "@/runtime";

const props = defineProps<{ settings: PlaygroundModelSource; busy: boolean; notice: string }>();
const emit = defineEmits<{ apply: [settings: PlaygroundModelSource]; clearCache: [] }>();
const mode = ref(props.settings.mode);
const modelBaseUrl = ref(props.settings.modelBaseUrl);
const persistent = ref(props.settings.persistent);
const validation = ref("");
watch(
  () => props.settings,
  (settings) => {
    mode.value = settings.mode;
    modelBaseUrl.value = settings.modelBaseUrl;
    persistent.value = settings.persistent;
  },
);
function apply() {
  validation.value = "";
  if (mode.value === "remote") {
    if (!modelBaseUrl.value.trim()) {
      validation.value = "Enter the model resource URL.";
      return;
    }
    try {
      const url = new URL(modelBaseUrl.value.trim(), document.baseURI);
      if (!["http:", "https:"].includes(url.protocol) || url.search || url.hash)
        throw new Error("Invalid resource directory URL");
    } catch {
      validation.value = "Use an HTTP(S) or relative directory URL without a query or fragment.";
      return;
    }
  }
  emit("apply", {
    mode: mode.value,
    modelBaseUrl: modelBaseUrl.value.trim(),
    persistent: persistent.value,
  });
}
</script>

<template>
  <details class="model-delivery">
    <summary class="model-delivery__summary">
      <span>Model loading</span>
      <span class="model-delivery__current">{{
        settings.mode === "local" ? "Website assets" : "Remote host"
      }}</span>
      <AppIcon name="chevronDown" :size="12" />
    </summary>
    <form class="model-delivery__form" @submit.prevent="apply">
      <label class="model-delivery__field">
        <span>Model source</span>
        <select v-model="mode" aria-label="Model source" :disabled="busy">
          <option value="local">Website assets</option>
          <option value="remote">Remote host</option>
        </select>
      </label>
      <label v-if="mode === 'remote'" class="model-delivery__field model-delivery__url">
        <span>Model resource URL</span>
        <input
          v-model="modelBaseUrl"
          type="text"
          inputmode="url"
          autocomplete="off"
          spellcheck="false"
          placeholder="https://storage.example.com/highlighting/"
          aria-describedby="model-delivery-hint"
        />
      </label>
      <label class="model-delivery__remember"
        ><input v-model="persistent" type="checkbox" :disabled="busy" />Remember downloads</label
      >
      <div class="model-delivery__actions">
        <button type="submit" :disabled="busy">Apply</button>
        <button type="button" :disabled="busy" @click="emit('clearCache')">
          {{ busy ? "Clearing…" : "Clear model cache" }}
        </button>
      </div>
      <p id="model-delivery-hint" class="model-delivery__hint">
        Inference stays in your browser. Remote URLs point to the exported model directory.
      </p>
      <p v-if="validation" class="model-delivery__error" role="alert">{{ validation }}</p>
      <p v-if="notice" class="model-delivery__hint" role="status">{{ notice }}</p>
    </form>
  </details>
</template>

<style scoped lang="scss">
.model-delivery {
  margin-block-end: 16px;
  color: var(--foreground);
  font-size: 12px;
}
.model-delivery__summary {
  display: flex;
  align-items: center;
  gap: 10px;
  width: fit-content;
  padding: 6px 0;
  cursor: pointer;
  list-style: none;
}
.model-delivery__summary::-webkit-details-marker {
  display: none;
}
.model-delivery__current,
.model-delivery__hint {
  color: var(--muted);
}
.model-delivery__form {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 14px;
  padding-block: 12px 4px;
}
.model-delivery__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.model-delivery__url {
  flex: 1;
  min-width: min(100%, 240px);
}
.model-delivery__remember {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
}
.model-delivery__actions {
  display: flex;
  gap: 8px;
}
select,
input[type="text"],
button {
  min-height: 34px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--foreground);
  padding: 6px 10px;
  font: inherit;
}
input[type="checkbox"] {
  accent-color: var(--focus);
}
input[type="text"] {
  width: 100%;
  min-width: 0;
  caret-color: var(--focus);
}
input::placeholder {
  color: var(--muted);
}
button {
  cursor: pointer;
}
button:hover {
  background: var(--button-hover);
}
button:disabled,
select:disabled {
  opacity: 0.55;
  cursor: default;
}
button:focus-visible,
select:focus-visible,
input:focus-visible,
summary:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 3px;
}
.model-delivery__hint,
.model-delivery__error {
  flex-basis: 100%;
  margin: 0;
  line-height: 1.5;
  overflow-wrap: anywhere;
}
.model-delivery__error {
  color: var(--error);
}
@media (max-width: 600px) {
  select,
  input[type="text"] {
    font-size: 16px;
  }
  .model-delivery__form {
    gap: 12px;
  }
  .model-delivery__url {
    flex-basis: 100%;
  }
}
</style>
