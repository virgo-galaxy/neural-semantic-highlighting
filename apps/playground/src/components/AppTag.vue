<script setup lang="ts">
withDefaults(
  defineProps<{
    tone?: "neutral" | "accent" | "success";
  }>(),
  {
    tone: "neutral",
  },
);
</script>

<template>
  <span class="app-tag" :data-tone="tone">
    <slot />
  </span>
</template>

<style scoped lang="scss">
.app-tag {
  display: inline-flex;
  align-items: center;

  height: 24px;
  padding: 0 9px;

  border: 1px solid var(--tag-border);
  border-radius: 999px;

  background: var(--tag-background);
  color: var(--muted);

  font-size: 11px;
  font-weight: 500;
  line-height: 1.25;

  white-space: nowrap;
}

.app-tag[data-tone="accent"] {
  border-color: color-mix(in srgb, var(--focus) 28%, transparent);

  background: color-mix(in srgb, var(--focus) 10%, transparent);
  color: var(--focus);
}

.app-tag[data-tone="success"] {
  border-color: var(--tag-success-border);
  background: var(--tag-success-background);
  color: var(--tag-success-foreground);
}
</style>
