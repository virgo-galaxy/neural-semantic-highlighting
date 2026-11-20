<script setup lang="ts">
import { ref } from "vue";

interface Props {
  title?: string;
  initialCount?: number;
}

const props = withDefaults(defineProps<Props>(), {
  title: "A new chapter",
  initialCount: 0,
});
const emit = defineEmits<{ (event: "change", count: number): void }>();
const count = ref(props.initialCount);

function increment() {
  count.value += 1;
  emit("change", count.value);
}

defineExpose({ increment });
</script>

<template>
  <h2>{{ props.title }}</h2>
  <button @click="increment">{{ count }}</button>
</template>
