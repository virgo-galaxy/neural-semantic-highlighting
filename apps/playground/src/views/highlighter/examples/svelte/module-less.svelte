<script module lang="ts">
  export const version: string = "1.0";
</script>
<script lang="ts">
  let name: string = "Orbit";
</script>

<div class="panel">
  <label>Name <input bind:value={name} /></label>
  <p>{name} — {version}</p>
</div>

<style lang="less">
  @space: 12px;
  .panel { padding: @space; border: 1px solid #ddd; }
</style>
