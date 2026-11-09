<script setup lang="ts">
import "@/layouts/styles/index.scss";

import { themes } from "@nsh/highlighter/themes";
import { ref } from "vue";

import AppHeader from "@/layouts/components/AppHeader.vue";
import type { AppTheme } from "@/layouts/types";

const theme = ref<AppTheme>("light");
const preset = ref("default");

function setTheme(nextTheme: AppTheme): void {
  theme.value = nextTheme;
}
function setPreset(value: string): void {
  if (themes.some((item) => item.id === value)) preset.value = value;
}
</script>

<template>
  <main class="app-page" :data-nsh-theme="theme" :data-nsh-preset="preset">
    <div class="app-shell">
      <AppHeader
        :theme="theme"
        :preset="preset"
        @theme-change="setTheme"
        @preset-change="setPreset"
      />

      <div class="app-content">
        <slot />
      </div>
    </div>
  </main>
</template>
