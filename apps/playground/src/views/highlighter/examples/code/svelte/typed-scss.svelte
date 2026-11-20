<script lang="ts">
  type Item = { title: string; visible: boolean };
  let item: Item = $state({ title: "星空 🌌", visible: true });
</script>

{#if item.visible}
  <aside class="notice">{item.title} &amp; beyond</aside>
{/if}

<style lang="scss">
  $accent: #a855f7;
  .notice {
    color: $accent;
    &:hover { opacity: 0.8; }
  }
</style>
