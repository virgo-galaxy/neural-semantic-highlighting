<script setup lang="ts">
import { TooltipArrow, TooltipContent, TooltipPortal, TooltipRoot, TooltipTrigger } from "reka-ui";

defineProps<{
  text: string;
}>();
</script>

<template>
  <TooltipRoot>
    <TooltipTrigger as-child>
      <slot />
    </TooltipTrigger>

    <TooltipPortal>
      <TooltipContent class="app-tooltip-content" side="top" align="center" :side-offset="8">
        {{ text }}

        <TooltipArrow class="app-tooltip-arrow" :width="10" :height="5" />
      </TooltipContent>
    </TooltipPortal>
  </TooltipRoot>
</template>

<style lang="scss">
.app-tooltip-content {
  z-index: 1000;

  padding: 6px 8px;

  border: 0;
  border-radius: 6px;

  background: var(--tooltip-background);
  color: var(--tooltip-foreground);

  box-shadow: var(--overlay-shadow);

  font-size: 12px;
  font-weight: 500;
  line-height: 1.25;

  white-space: nowrap;
  user-select: none;

  animation: app-tooltip-in 120ms ease-out;
}

.app-tooltip-arrow {
  fill: var(--tooltip-background);
  color: var(--tooltip-background);

  transform: translateY(-1px);
}

@keyframes app-tooltip-in {
  from {
    opacity: 0;
    transform: translateY(2px) scale(0.98);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
