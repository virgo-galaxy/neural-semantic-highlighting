<script setup lang="ts">
import UiProvider from "@/components/UiProvider.vue";
import AppLayout from "@/layouts/AppLayout.vue";
import HighlighterView from "@/views/highlighter/HighlighterView.vue";
</script>

<template>
  <UiProvider>
    <AppLayout>
      <HighlighterView />
    </AppLayout>
  </UiProvider>
</template>
