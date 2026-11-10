<script>
  let request = Promise.resolve({ message: "Hello, Svelte!" });
</script>

{#await request}
  <p>Loading…</p>
{:then result}
  <article>{result.message}</article>
{:catch error}
  <p class="error">{error.message}</p>
{/await}
