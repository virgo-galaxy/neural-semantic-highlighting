<script lang="ts">
  let count = $state(0);
  const doubled = $derived(count * 2);

  function increment() {
    count += 1;
  }
</script>

<button onclick={increment}>Count: {count}</button>
<p>Doubled: {doubled}</p>

<style>
  button {
    color: white;
    background: #6754db;
    padding: 8px 16px;
    border-radius: 8px;
  }
</style>
