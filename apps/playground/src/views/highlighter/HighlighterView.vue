<script setup lang="ts">
import "@/views/highlighter/styles/index.scss";

import { onMounted } from "vue";

import HighlightBlock from "@/views/highlighter/components/HighlightBlock.vue";
import ModelDeliveryControls from "@/views/highlighter/components/ModelDeliveryControls.vue";
import { useHighlighter } from "@/views/highlighter/composables/useHighlighter";

const {
  source,
  state,
  previewHtml,
  errorMessage,
  lastHighlightMs,
  contentTypes,
  currentContentTypeId,
  currentFilename,
  setContentType,
  beginEditing,
  markSourceChanged,
  finishEditing,
  loadRandomExample,
  highlightCurrentSource,
  deliverySettings,
  cacheBusy,
  cacheNotice,
  setModelSource,
  clearDownloadedModels,
} = useHighlighter();

onMounted(() => {
  void highlightCurrentSource();
});
</script>

<template>
  <ModelDeliveryControls
    :settings="deliverySettings"
    :busy="cacheBusy"
    :notice="cacheNotice"
    @apply="setModelSource"
    @clear-cache="clearDownloadedModels"
  />
  <HighlightBlock
    v-model="source"
    :state="state"
    :preview-html="previewHtml"
    :error-message="errorMessage"
    :filename="currentFilename"
    :last-highlight-ms="lastHighlightMs"
    :content-type-id="currentContentTypeId"
    :content-types="contentTypes"
    @content-type-change="setContentType"
    @random-example="loadRandomExample"
    @begin-editing="beginEditing"
    @source-changed="markSourceChanged"
    @finish-editing="finishEditing"
    @retry="highlightCurrentSource"
  />
</template>
