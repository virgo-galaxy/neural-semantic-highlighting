<script setup lang="ts">
import { computed, type CSSProperties } from "vue";

import checkIcon from "@/assets/icons/check.svg";
import chevronDownIcon from "@/assets/icons/chevron-down.svg";
import moonIcon from "@/assets/icons/moon.svg";
import shuffleIcon from "@/assets/icons/shuffle.svg";
import sunIcon from "@/assets/icons/sun.svg";

const icons = {
  check: checkIcon,
  chevronDown: chevronDownIcon,
  moon: moonIcon,
  shuffle: shuffleIcon,
  sun: sunIcon,
} as const;

type IconName = keyof typeof icons;

const props = withDefaults(
  defineProps<{
    name: IconName;
    size?: number;
  }>(),
  {
    size: 16,
  },
);

const iconStyle = computed<CSSProperties>(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
  "--app-icon-url": `url("${icons[props.name]}")`,
}));
</script>

<template>
  <span class="app-icon" :style="iconStyle" aria-hidden="true"></span>
</template>

<style scoped lang="scss">
.app-icon {
  display: inline-block;
  flex: 0 0 auto;

  background: currentColor;

  -webkit-mask: var(--app-icon-url) center / contain no-repeat;
  mask: var(--app-icon-url) center / contain no-repeat;
}
</style>
