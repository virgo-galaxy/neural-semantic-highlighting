<template>
  <JournalPanel :expanded.sync="expanded" @click.native="openJournal">
    <h2 slot="heading">{{ title | uppercase }}</h2>
    <template slot="entry" slot-scope="{ entry }">
      <span>{{ entry.author }}: {{ entry.title }}</span>
    </template>
    <button v-if="expanded" @click.stop="save">Save changes</button>
  </JournalPanel>
</template>

<script>
export default {
  name: "JournalOverview",
  data() {
    return { title: "Weekend journal", expanded: true };
  },
  filters: {
    uppercase(value) {
      return String(value).toUpperCase();
    },
  },
  methods: {
    openJournal() {
      this.expanded = true;
    },
    save() {
      this.$emit("save", this.title);
    },
  },
};
</script>
