import { clearModelCache } from "@nsh/highlighter";
import { renderToHtml } from "@nsh/html";
import { computed, onBeforeUnmount, ref } from "vue";

import {
  defaultModelSource,
  type PlaygroundModelSource,
  PlaygroundRuntimeManager,
} from "@/runtime";
import {
  examplesForContentType,
  highlighterContentTypes,
  type HighlighterExample,
} from "@/views/highlighter/examples";
import type { HighlightState } from "@/views/highlighter/types";

function defaultContentTypeId(): string {
  return (
    highlighterContentTypes.find((language) => language.id === "typescript")?.id ??
    highlighterContentTypes[0]?.id ??
    "typescript"
  );
}

function defaultExampleIndex(examples: readonly HighlighterExample[]): number {
  const helloIndex = examples.findIndex((example) =>
    example.filename.toLowerCase().startsWith("hello."),
  );

  return helloIndex >= 0 ? helloIndex : 0;
}

export function useHighlighter() {
  const currentContentTypeId = ref(defaultContentTypeId());
  const exampleIndex = ref(0);
  const state = ref<HighlightState>("pending");
  const previewHtml = ref("");
  const errorMessage = ref("");
  const lastHighlightMs = ref<number | null>(null);
  const deliverySettings = ref<PlaygroundModelSource>({ ...defaultModelSource });
  const cacheBusy = ref(false);
  const cacheNotice = ref("");
  const runtime = new PlaygroundRuntimeManager();

  const currentExamples = computed(() => examplesForContentType(currentContentTypeId.value));

  exampleIndex.value = defaultExampleIndex(currentExamples.value);

  const currentExample = computed(() => currentExamples.value[exampleIndex.value]);
  const source = ref(currentExample.value?.source ?? "");

  let revision = 0;
  let disposed = false;
  onBeforeUnmount(() => {
    disposed = true;
    revision += 1;
    runtime.close();
  });

  const currentFilename = computed(() => currentExample.value?.filename ?? "custom");

  function setModelSource(settings: PlaygroundModelSource): void {
    deliverySettings.value = { ...settings };
    cacheNotice.value = "";
    runtime.reset();
    void highlightCurrentSource();
  }

  async function clearDownloadedModels(): Promise<void> {
    if (cacheBusy.value) return;
    cacheBusy.value = true;
    revision++;
    runtime.reset();
    try {
      const removed = await clearModelCache();
      if (disposed) return;
      cacheNotice.value = removed
        ? "Downloaded model cache cleared."
        : "No stored model cache, or browser storage is unavailable.";
    } finally {
      cacheBusy.value = false;
    }
    if (!disposed) void highlightCurrentSource();
  }

  function beginEditing(): void {
    revision += 1;
    state.value = "editing";
    errorMessage.value = "";
  }

  function markSourceChanged(): void {
    revision += 1;
  }

  function finishEditing(): void {
    void highlightCurrentSource();
  }

  function setContentType(contentTypeId: string): void {
    if (contentTypeId === currentContentTypeId.value) {
      return;
    }

    const examples = examplesForContentType(contentTypeId);

    if (examples.length === 0) {
      return;
    }

    currentContentTypeId.value = contentTypeId;
    exampleIndex.value = defaultExampleIndex(examples);
    source.value = examples[exampleIndex.value]?.source ?? "";

    revision += 1;

    void highlightCurrentSource();
  }

  function loadRandomExample(): void {
    const examples = currentExamples.value;

    if (examples.length < 2) {
      return;
    }

    const offset = 1 + Math.floor(Math.random() * (examples.length - 1));
    const nextIndex = (exampleIndex.value + offset) % examples.length;
    const nextExample = examples[nextIndex];

    if (!nextExample) {
      return;
    }

    exampleIndex.value = nextIndex;
    revision += 1;
    source.value = nextExample.source;

    void highlightCurrentSource();
  }

  async function highlightCurrentSource(): Promise<void> {
    const requestRevision = ++revision;
    const requestSource = source.value;
    const documentKind = currentExample.value?.documentKind ?? currentContentTypeId.value;
    const startedAt = performance.now();

    state.value = "pending";
    errorMessage.value = "";

    try {
      const highlighter = await runtime.get(deliverySettings.value);

      const result = await highlighter.highlight({
        source: requestSource,
        documentKind,
      });

      if (disposed || revision !== requestRevision) {
        return;
      }

      previewHtml.value = renderToHtml({
        source: requestSource,
        documentKind,
        result,
      });

      lastHighlightMs.value = Math.max(1, Math.round(performance.now() - startedAt));
      state.value = "highlighted";
    } catch (error) {
      if (disposed || revision !== requestRevision) {
        return;
      }

      errorMessage.value = error instanceof Error ? error.message : "Unable to highlight source.";
      state.value = "error";
    }
  }

  return {
    source,
    state,
    previewHtml,
    errorMessage,
    lastHighlightMs,
    contentTypes: highlighterContentTypes,
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
  };
}
