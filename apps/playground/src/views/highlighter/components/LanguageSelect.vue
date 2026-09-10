<script setup lang="ts">
import { computed } from "vue";

import AppSelect from "@/components/AppSelect.vue";
import type { HighlighterLanguage } from "@/views/highlighter/examples";

const props = defineProps<{
  modelValue: string;
  languages: readonly HighlighterLanguage[];
}>();

const emit = defineEmits<{
  "update:modelValue": [languageId: string];
}>();

const options = computed(() =>
  props.languages.map((language) => ({
    value: language.id,
    label: language.label,
    icon: language.icon,
  })),
);
</script>

<template>
  <AppSelect
    :model-value="props.modelValue"
    :options="options"
    ariaLabel="Select language"
    @update:model-value="emit('update:modelValue', $event)"
  />
</template>
