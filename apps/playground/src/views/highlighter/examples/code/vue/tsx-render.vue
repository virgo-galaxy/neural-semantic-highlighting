<script lang="tsx">
import { defineComponent, ref } from "vue";

export default defineComponent({
  setup() {
    const count = ref(0);
    return () => (
      <button class="counter" onClick={() => count.value++}>
        Ideas: {count.value}
      </button>
    );
  },
});
</script>

<style scoped>
.counter {
  padding: 8px 16px;
}
</style>
