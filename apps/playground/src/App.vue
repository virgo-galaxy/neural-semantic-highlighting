<script setup lang="ts">
import { createHighlighter, type SemanticPack } from "@nsh/core";
import { renderToHtml } from "@nsh/html";
import { onMounted, ref } from "vue";

const source = "const value = 1;";
const documentKind = "typescript";

const previewHtml = ref("");
const errorMessage = ref("");

const examplePack: SemanticPack = {
  manifest: {
    id: "example",
    documentKinds: [
      {
        id: "typescript",
        extensions: [".ts"],
      },
    ],
  },

  async highlight(request) {
    if (request.source !== source) {
      throw new Error("This example pack only supports the built-in sample.");
    }

    return {
      offsetEncoding: "utf-16",
      spans: [
        { start: 0, end: 5, tokenType: "keyword" },
        {
          start: 6,
          end: 11,
          tokenType: "variable",
          modifiers: ["declaration", "readonly"],
        },
        { start: 12, end: 13, tokenType: "operator" },
        { start: 14, end: 15, tokenType: "number" },
        { start: 15, end: 16, tokenType: "punctuation" },
      ],
    };
  },
};

const highlighter = createHighlighter({
  packs: [examplePack],
});

onMounted(async () => {
  try {
    const result = await highlighter.highlight({
      source,
      documentKind,
    });

    previewHtml.value = renderToHtml({
      source,
      documentKind,
      result,
    });
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Unable to render the example.";
  }
});
</script>

<template>
  <main class="playground">
    <header class="playground-header">
      <p class="eyebrow">Neural Semantic Highlighting</p>
      <h1>Playground</h1>
      <p class="description">Powered by NSH Core, the HTML renderer, and CSS themes.</p>
      <p class="notice">Fixed sample only. Model inference is not connected yet.</p>
    </header>

    <div class="panels">
      <section class="panel" aria-labelledby="source-heading">
        <h2 id="source-heading">Source</h2>
        <pre class="source-preview"><code>{{ source }}</code></pre>
      </section>

      <section class="panel" aria-labelledby="preview-heading">
        <h2 id="preview-heading">Highlighted output</h2>

        <p v-if="errorMessage" class="error-message" role="alert">
          {{ errorMessage }}
        </p>
        <p v-else-if="!previewHtml" role="status">Rendering preview...</p>

        <!-- Only render HTML produced by @nsh/html, never raw source text. -->
        <div v-else class="highlight-preview" v-html="previewHtml"></div>
      </section>
    </div>
  </main>
</template>
