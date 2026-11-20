<script>
  export let title = "Welcome";
  let selected = false;
  $: label = selected ? "Selected" : "Choose";
</script>

<section class:active={selected}>
  <h2>{title}</h2>
  <button on:click={() => selected = !selected}>{label}</button>
  <slot name="description">Choose an item to continue.</slot>
</section>
