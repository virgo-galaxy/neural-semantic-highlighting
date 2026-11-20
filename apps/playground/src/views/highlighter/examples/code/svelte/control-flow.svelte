<script lang="ts">
  let people = [{ id: 1, name: "Ada" }, { id: 2, name: "Lin" }];
  let ready = true;
</script>

{#if ready}
  <ul>
    {#each people as person, index (person.id)}
      <li>{index + 1}. {person.name}</li>
    {:else}
      <li>No people yet</li>
    {/each}
  </ul>
{:else}
  <p>Please wait…</p>
{/if}
