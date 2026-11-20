<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";

import AppIcon from "@/components/AppIcon.vue";
import AppTag from "@/components/AppTag.vue";
import AppTooltip from "@/components/AppTooltip.vue";
import ContentTypeSelect from "@/views/highlighter/components/ContentTypeSelect.vue";
import HighlightStatus from "@/views/highlighter/components/HighlightStatus.vue";
import type { HighlighterContentType } from "@/views/highlighter/examples";
import type { HighlightState } from "@/views/highlighter/types";

const source = defineModel<string>({ required: true });

const props = defineProps<{
  state: HighlightState;
  previewHtml: string;
  errorMessage: string;
  filename: string;
  lastHighlightMs: number | null;
  contentTypeId: string;
  contentTypes: readonly HighlighterContentType[];
}>();

const emit = defineEmits<{
  beginEditing: [];
  sourceChanged: [];
  finishEditing: [];
  contentTypeChange: [contentTypeId: string];
  randomExample: [];
}>();

const editor = ref<HTMLTextAreaElement | null>(null);

const contentTypeLabel = computed(
  () => props.contentTypes.find((language) => language.id === props.contentTypeId)?.label ?? "Code",
);

watch(
  () => props.state,
  (state) => {
    if (state !== "editing") {
      return;
    }

    void nextTick(() => {
      editor.value?.focus();
    });
  },
);
</script>

<template>
  <section class="highlight-block" :aria-label="`${contentTypeLabel} example`">
    <div class="highlight-block__toolbar">
      <div class="highlight-block__meta">
        <ContentTypeSelect
          :model-value="contentTypeId"
          :content-types="contentTypes"
          @update:model-value="emit('contentTypeChange', $event)"
        />

        <span class="highlight-block__divider" aria-hidden="true"></span>

        <div class="highlight-block__example-switcher">
          <AppTooltip text="Shuffle example">
            <button
              type="button"
              class="highlight-block__shuffle"
              aria-label="Shuffle example"
              @click="emit('randomExample')"
            >
              <AppIcon name="shuffle" :size="14" />
            </button>
          </AppTooltip>

          <span class="highlight-block__filename" :title="filename">
            {{ filename }}
          </span>
        </div>
      </div>

      <div class="highlight-block__status">
        <AppTag tone="success">Browser</AppTag>

        <HighlightStatus :state="state" :latency-ms="lastHighlightMs" />
      </div>
    </div>

    <textarea
      v-show="state === 'editing'"
      ref="editor"
      v-model="source"
      class="highlight-block__editor nsh"
      :data-language="contentTypeId"
      :aria-label="`${contentTypeLabel} source`"
      spellcheck="false"
      @input="emit('sourceChanged')"
      @blur="emit('finishEditing')"
    ></textarea>

    <div
      v-show="state !== 'editing'"
      class="highlight-block__surface"
      role="button"
      tabindex="0"
      :aria-busy="state === 'pending'"
      :aria-label="`Click to edit ${contentTypeLabel} source`"
      @click="emit('beginEditing')"
      @keydown.enter="emit('beginEditing')"
      @keydown.space.prevent="emit('beginEditing')"
    >
      <div
        v-if="state === 'highlighted'"
        class="highlight-block__preview"
        v-html="previewHtml"
      ></div>

      <pre
        v-else
        class="highlight-block__source nsh"
        :data-language="contentTypeId"
      ><code>{{ source }}</code></pre>
    </div>

    <div class="highlight-block__footer" :data-state="state">
      <p v-if="errorMessage" class="highlight-block__error" role="alert" :title="errorMessage">
        {{ errorMessage }}
      </p>

      <p v-else class="highlight-block__hint">
        Click the block to edit. Highlighting runs when it loses focus.
      </p>
    </div>
  </section>
</template>
