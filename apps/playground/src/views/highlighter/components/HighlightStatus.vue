<script setup lang="ts">
import { computed } from "vue";

import type { HighlightState } from "@/views/highlighter/types";

type PerformanceLevel = "idle" | "pending" | "fast" | "warning" | "critical";

const props = defineProps<{
  state: HighlightState;
  latencyMs: number | null;
}>();

const statusText = computed(() => {
  switch (props.state) {
    case "editing":
      return "Editing";

    case "pending":
      return "Highlighting";

    case "highlighted":
      return "Highlighted";

    case "error":
      return "Error";

    default:
      return "Unknown";
  }
});

const performanceLevel = computed<PerformanceLevel>(() => {
  if (props.state === "editing") {
    return "idle";
  }

  if (props.state === "pending") {
    return "pending";
  }

  if (props.state === "error") {
    return "critical";
  }

  if (props.latencyMs === null) {
    return "idle";
  }

  if (props.latencyMs <= 100) {
    return "fast";
  }

  if (props.latencyMs <= 250) {
    return "warning";
  }

  return "critical";
});

const isBreathing = computed(() => props.state === "pending" || props.state === "highlighted");

const ariaLabel = computed(() => {
  if (props.state === "highlighted" && props.latencyMs !== null) {
    return `Highlighted in ${props.latencyMs} milliseconds`;
  }

  return statusText.value;
});
</script>

<template>
  <div
    class="status-label highlight-status"
    :data-state="props.state"
    :data-performance="performanceLevel"
    :data-breathing="isBreathing"
    role="status"
    :aria-label="ariaLabel"
  >
    <span class="highlight-status__dot" aria-hidden="true"></span>

    <span class="highlight-status__label">
      {{ statusText }}
    </span>

    <span class="highlight-status__divider" aria-hidden="true"></span>

    <span class="highlight-status__latency">
      <template v-if="props.state === 'highlighted' && props.latencyMs !== null">
        <span class="highlight-status__latency-value">
          {{ props.latencyMs }}
        </span>

        <span class="highlight-status__latency-unit"> ms </span>
      </template>

      <span v-else class="highlight-status__latency-placeholder"> — </span>
    </span>
  </div>
</template>
