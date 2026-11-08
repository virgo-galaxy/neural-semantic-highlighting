<script setup lang="ts">
const tone = "royalblue";
</script>

<template>
  <article :class="$style.card" class="journal">
    <h2>Room for an idea</h2>
    <slot>Start writing here.</slot>
  </article>
</template>

<style scoped lang="scss">
$space: 16px;
.journal {
  display: grid;
  gap: $space;
  color: v-bind(tone);
}
</style>

<style module lang="less">
@radius: 12px;
.card {
  border-radius: @radius;
  padding: 24px;
}
</style>
