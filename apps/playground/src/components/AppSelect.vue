<script setup lang="ts">
import {
  SelectContent,
  SelectItem,
  SelectItemIndicator,
  SelectItemText,
  SelectPortal,
  SelectRoot,
  SelectTrigger,
  SelectValue,
  SelectViewport,
} from "reka-ui";
import { computed } from "vue";

import AppIcon from "@/components/AppIcon.vue";

interface SelectOption {
  value: string;
  label: string;
  icon?: string;
}

const props = defineProps<{
  modelValue: string;
  options: readonly SelectOption[];
  ariaLabel: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const hasIcons = computed(() => props.options.some((option) => option.icon));

const selectedOption = computed(() =>
  props.options.find((option) => option.value === props.modelValue),
);

function handleValueChange(value: unknown): void {
  if (typeof value === "string") {
    emit("update:modelValue", value);
  }
}
</script>

<template>
  <SelectRoot :model-value="props.modelValue" @update:model-value="handleValueChange">
    <SelectTrigger
      class="app-select-trigger"
      :class="{ 'app-select-trigger--plain': !hasIcons }"
      :aria-label="props.ariaLabel"
    >
      <img
        v-if="selectedOption?.icon"
        class="app-select-trigger-icon"
        :src="selectedOption.icon"
        alt=""
        aria-hidden="true"
      />

      <SelectValue class="app-select-value" />

      <AppIcon class="app-select-chevron" name="chevronDown" :size="12" />
    </SelectTrigger>

    <SelectPortal>
      <SelectContent
        class="app-select-content"
        :class="{ 'app-select-content--plain': !hasIcons }"
        position="popper"
        side="bottom"
        align="start"
        :side-offset="7"
      >
        <SelectViewport class="app-select-viewport">
          <SelectItem
            v-for="option in props.options"
            :key="option.value"
            class="app-select-item"
            :value="option.value"
          >
            <span v-if="hasIcons" class="app-select-item-icon-slot" aria-hidden="true">
              <img v-if="option.icon" class="app-select-item-icon" :src="option.icon" alt="" />
            </span>

            <SelectItemText class="app-select-item-label">
              {{ option.label }}
            </SelectItemText>

            <span class="app-select-indicator-slot">
              <SelectItemIndicator class="app-select-indicator">
                <AppIcon name="check" :size="13" />
              </SelectItemIndicator>
            </span>
          </SelectItem>
        </SelectViewport>
      </SelectContent>
    </SelectPortal>
  </SelectRoot>
</template>

<style lang="scss">
.app-select-trigger {
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr) 12px;
  align-items: center;

  width: 116px;
  height: 26px;
  flex: 0 0 116px;

  gap: 5px;
  margin: 0;
  padding: 0 6px;

  border: 0;
  border-radius: 6px;
  outline: none;

  background: transparent;
  color: var(--foreground);

  font: inherit;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;

  cursor: pointer;

  transition:
    background-color 120ms ease,
    color 120ms ease;
}

.app-select-trigger:hover,
.app-select-trigger[data-state="open"] {
  background: var(--button-hover);
}

.app-select-trigger:focus,
.app-select-trigger:focus-visible {
  outline: none;
  box-shadow: none;
}

.app-select-trigger:focus-visible {
  background: var(--button-hover);
}

.app-select-trigger-icon {
  display: block;

  width: 14px;
  height: 14px;

  object-fit: contain;
}

.app-select-value {
  min-width: 0;

  overflow: hidden;

  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-select-chevron {
  width: 12px;
  height: 12px;

  color: var(--muted);

  transition: transform 120ms ease;
}

.app-select-trigger[data-state="open"] .app-select-chevron {
  transform: rotate(180deg);
}

.app-select-content {
  z-index: 1000;

  min-width: max(164px, var(--reka-select-trigger-width));
  max-height: var(--reka-select-content-available-height);

  overflow: hidden;

  padding: 5px;

  border: 1px solid var(--overlay-border);
  border-radius: 10px;

  background: var(--overlay-background);
  color: var(--foreground);

  -webkit-backdrop-filter: blur(20px) saturate(150%);
  backdrop-filter: blur(20px) saturate(150%);

  box-shadow: var(--overlay-shadow);

  transform-origin: var(--reka-select-content-transform-origin);

  animation: app-select-in 120ms ease-out;

  -webkit-user-select: none;
  user-select: none;
}

.app-select-viewport {
  padding: 0;
}

.app-select-item {
  position: relative;

  display: grid;
  grid-template-columns: 18px minmax(0, 1fr) 18px;
  align-items: center;

  gap: 7px;
  min-height: 32px;

  padding: 0 8px;

  border: 0;
  border-radius: 7px;
  outline: none;

  background: transparent;
  color: var(--foreground);

  font: inherit;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.2;

  cursor: pointer;

  -webkit-user-select: none;
  user-select: none;

  transition:
    background-color 120ms ease,
    color 120ms ease;
}

.app-select-item[data-highlighted] {
  background: var(--button-hover);
}

.app-select-item[data-state="checked"] {
  background: transparent;
  color: var(--focus);
  font-weight: 600;
}

.app-select-item[data-state="checked"][data-highlighted] {
  background: var(--button-hover);
  color: var(--focus);
}

.app-select-item-icon-slot,
.app-select-indicator-slot {
  display: grid;

  width: 18px;
  height: 18px;

  place-items: center;
}

.app-select-item-icon {
  display: block;

  width: 15px;
  height: 15px;

  object-fit: contain;
}

.app-select-item-label {
  min-width: 0;

  overflow: hidden;

  color: inherit;

  font: inherit;

  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-select-indicator {
  display: grid;

  width: 14px;
  height: 14px;

  place-items: center;

  color: var(--focus);
}

.app-select-trigger--plain {
  grid-template-columns: minmax(0, 1fr) 12px;
}
.app-select-content--plain .app-select-item {
  grid-template-columns: minmax(0, 1fr) 18px;
}

@keyframes app-select-in {
  from {
    opacity: 0;
    transform: translateY(-2px) scale(0.98);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
