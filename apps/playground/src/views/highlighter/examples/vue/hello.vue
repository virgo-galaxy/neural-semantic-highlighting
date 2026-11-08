<script setup lang="ts">
import { ref } from "vue";

const title = "Team journal";
const entries = ref(0);

function addEntry() {
  entries.value += 1;
}
</script>

<template>
  <section class="journal">
    <h1>{{ title }}</h1>
    <p>{{ entries }} ideas saved</p>
    <button type="button" @click="addEntry">Add an idea</button>
  </section>
</template>

<style scoped>
.journal {
  display: grid;
  gap: 16px;
}
</style>
