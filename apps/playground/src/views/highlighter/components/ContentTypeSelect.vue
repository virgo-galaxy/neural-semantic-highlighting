<script setup lang="ts">
import { contentCategories } from "@nsh/highlighter/catalog";
import { computed } from "vue";

import AppSelect from "@/components/AppSelect.vue";
import type { HighlighterContentType } from "@/views/highlighter/examples";

const props = defineProps<{
  modelValue: string;
  contentTypes: readonly HighlighterContentType[];
}>();

const emit = defineEmits<{
  "update:modelValue": [contentTypeId: string];
}>();

const options = computed(() =>
  props.contentTypes.map((entry) => ({
    value: entry.id,
    label: entry.label,
    icon: entry.icon,
    group: contentCategories.find((category) => category.id === entry.category)!.label,
  })),
);
</script>

<template>
  <AppSelect
    :model-value="props.modelValue"
    :options="options"
    ariaLabel="Select content type"
    @update:model-value="emit('update:modelValue', $event)"
  />
</template>
