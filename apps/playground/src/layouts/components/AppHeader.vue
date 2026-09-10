<script setup lang="ts">
import AppIcon from "@/components/AppIcon.vue";
import AppTooltip from "@/components/AppTooltip.vue";
import type { AppTheme } from "@/layouts/types";

defineProps<{
  theme: AppTheme;
}>();

const emit = defineEmits<{
  themeChange: [theme: AppTheme];
}>();
</script>

<template>
  <header class="app-header">
    <div class="app-header__top">
      <div class="app-brand">
        <img class="app-brand__mark" src="/favicon.svg" alt="" aria-hidden="true" />

        <div class="app-brand__copy">
          <p class="app-brand__eyebrow">Neural Semantic Highlighting</p>
          <h1 class="app-brand__title">Playground</h1>
        </div>
      </div>

      <div class="app-header__actions">
        <div class="theme-switch" role="group" aria-label="Color theme">
          <AppTooltip text="Light theme">
            <button
              type="button"
              class="theme-switch__button"
              :class="{ 'theme-switch__button--active': theme === 'light' }"
              :aria-pressed="theme === 'light'"
              aria-label="Use light theme"
              @click="emit('themeChange', 'light')"
            >
              <AppIcon name="sun" :size="17" />
            </button>
          </AppTooltip>

          <AppTooltip text="Dark theme">
            <button
              type="button"
              class="theme-switch__button"
              :class="{ 'theme-switch__button--active': theme === 'dark' }"
              :aria-pressed="theme === 'dark'"
              aria-label="Use dark theme"
              @click="emit('themeChange', 'dark')"
            >
              <AppIcon name="moon" :size="17" />
            </button>
          </AppTooltip>
        </div>
      </div>
    </div>

    <p class="app-header__description">
      A runtime-agnostic neural semantic highlighting engine with pluggable language packs, model
      runtimes, and renderers.
    </p>
  </header>
</template>
