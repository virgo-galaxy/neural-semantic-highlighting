<script lang="ts">
  let { heading = "Inventory" } = $props();
  let rows = [{ name: "Keyboard", stock: 12 }];
</script>

{#snippet product(name, stock)}
  <tr><td>{name}</td><td>{stock}</td></tr>
{/snippet}

<h2>{heading}</h2>
<table>
  <tbody>
    {#each rows as row}
      {@render product(row.name, row.stock)}
    {/each}
  </tbody>
</table>
