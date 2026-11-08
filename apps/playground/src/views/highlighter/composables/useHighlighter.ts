import { createHighlighter, type Highlighter } from "@nsh/core";
import { renderToHtml } from "@nsh/html";
import { computed, onBeforeUnmount, ref } from "vue";

import { createBrowserSemanticPack } from "@/runtime";
import {
  examplesForLanguage,
  type HighlighterExample,
  highlighterLanguages,
} from "@/views/highlighter/examples";
import type { HighlightState } from "@/views/highlighter/types";

function defaultLanguageId(): string {
  return (
    highlighterLanguages.find((language) => language.id === "typescript")?.id ??
    highlighterLanguages[0]?.id ??
    "typescript"
  );
}

function defaultExampleIndex(examples: readonly HighlighterExample[]): number {
  const helloIndex = examples.findIndex((example) => example.filename.startsWith("hello."));

  return helloIndex >= 0 ? helloIndex : 0;
}

export function useHighlighter() {
  const currentLanguageId = ref(defaultLanguageId());
  const exampleIndex = ref(0);
  const state = ref<HighlightState>("pending");
  const previewHtml = ref("");
  const errorMessage = ref("");
  const lastHighlightMs = ref<number | null>(null);

  const currentExamples = computed(() => examplesForLanguage(currentLanguageId.value));

  exampleIndex.value = defaultExampleIndex(currentExamples.value);

  const currentExample = computed(() => currentExamples.value[exampleIndex.value]);
  const source = ref(currentExample.value?.source ?? "");

  let revision = 0;
  let disposed = false;
  let closePack: (() => void) | undefined;
  onBeforeUnmount(() => {
    disposed = true;
    revision += 1;
    closePack?.();
  });
  let highlighterPromise: Promise<Highlighter> | undefined;

  const currentFilename = computed(() => currentExample.value?.filename ?? "custom");

  function getHighlighter(): Promise<Highlighter> {
    highlighterPromise ??= createBrowserSemanticPack()
      .then((pack) => {
        closePack = () => pack.close();
        if (disposed) pack.close();
        return createHighlighter({ packs: [pack] });
      })
      .catch((error: unknown) => {
        highlighterPromise = undefined;
        throw error;
      });

    return highlighterPromise;
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

  function setLanguage(languageId: string): void {
    if (languageId === currentLanguageId.value) {
      return;
    }

    const examples = examplesForLanguage(languageId);

    if (examples.length === 0) {
      return;
    }

    currentLanguageId.value = languageId;
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
    const requestRevision = revision;
    const requestSource = source.value;
    const documentKind = currentExample.value?.documentKind ?? currentLanguageId.value;
    const startedAt = performance.now();

    state.value = "pending";
    errorMessage.value = "";

    try {
      const highlighter = await getHighlighter();

      const result = await highlighter.highlight({
        source: requestSource,
        documentKind,
      });

      if (revision !== requestRevision) {
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
      if (revision !== requestRevision) {
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
    languages: highlighterLanguages,
    currentLanguageId,
    currentFilename,
    setLanguage,
    beginEditing,
    markSourceChanged,
    finishEditing,
    loadRandomExample,
    highlightCurrentSource,
  };
}
