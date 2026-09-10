<script setup lang="ts">
import { TooltipProvider } from "reka-ui";
</script>

<template>
  <TooltipProvider
    :delay-duration="250"
    :skip-delay-duration="100"
    :ignore-non-keyboard-focus="true"
  >
    <slot />
  </TooltipProvider>
</template>
