<script>
  let email = "";
  let accepted = false;
  let disabled = false;
  let options = { autocomplete: "email" };
</script>

<form on:submit|preventDefault={() => console.log(email)}>
  <input type="email" bind:value={email} {...options} {disabled} />
  <label class:checked={accepted}>
    <input type="checkbox" bind:checked={accepted} />
    Accept terms &amp; conditions
  </label>
  <button disabled={!accepted}>Continue</button>
</form>
