<script>
import { computed, ref } from "vue";

export default {
  setup() {
    const query = ref("");
    const notes = ref(["A new place", "A small discovery", "An idea to share"]);
    const visibleNotes = computed(() => notes.value.filter((note) => note.includes(query.value)));
    return { query, visibleNotes };
  },
};
</script>

<template>
  <input v-model.trim="query" aria-label="Search notes" />
  <ul>
    <li v-for="note in visibleNotes" :key="note">{{ note }}</li>
  </ul>
  <Teleport to="body">
    <p v-if="visibleNotes.length === 0">No matching notes.</p>
  </Teleport>
</template>
