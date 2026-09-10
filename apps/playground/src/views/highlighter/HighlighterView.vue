<script setup lang="ts">
import "@/views/highlighter/styles/index.scss";

import { onMounted } from "vue";

import HighlightBlock from "@/views/highlighter/components/HighlightBlock.vue";
import { useHighlighter } from "@/views/highlighter/composables/useHighlighter";

const {
  source,
  state,
  previewHtml,
  errorMessage,
  lastHighlightMs,
  languages,
  currentLanguageId,
  currentFilename,
  setLanguage,
  beginEditing,
  markSourceChanged,
  finishEditing,
  loadRandomExample,
  highlightCurrentSource,
} = useHighlighter();

onMounted(() => {
  void highlightCurrentSource();
});
</script>

<template>
  <HighlightBlock
    v-model="source"
    :state="state"
    :preview-html="previewHtml"
    :error-message="errorMessage"
    :filename="currentFilename"
    :last-highlight-ms="lastHighlightMs"
    :language-id="currentLanguageId"
    :languages="languages"
    @language-change="setLanguage"
    @random-example="loadRandomExample"
    @begin-editing="beginEditing"
    @source-changed="markSourceChanged"
    @finish-editing="finishEditing"
  />
</template>
