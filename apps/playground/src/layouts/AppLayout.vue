<script setup lang="ts">
import "@/layouts/styles/index.scss";

import { ref } from "vue";

import AppHeader from "@/layouts/components/AppHeader.vue";
import type { AppTheme } from "@/layouts/types";

const theme = ref<AppTheme>("light");

function setTheme(nextTheme: AppTheme): void {
  theme.value = nextTheme;
}
</script>

<template>
  <main class="app-page" :data-nsh-theme="theme">
    <div class="app-shell">
      <AppHeader :theme="theme" @theme-change="setTheme" />

      <div class="app-content">
        <slot />
      </div>
    </div>
  </main>
</template>
