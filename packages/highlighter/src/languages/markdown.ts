import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "markdown",
  manifest: {
    id: "markdown",
    documentKinds: [
      {
        id: "markdown",
        extensions: [".md", ".markdown", ".mdown", ".mkd"],
      },
    ],
  },
  sha256: "68d79f17f6d37761dd77b8f8f67f43c939b138abae7f628bcab0042d8e0893f1",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "punctuation",
      "text",
      "entity",
      "heading",
      "link",
      "link-destination",
      "code",
      "code-fence",
      "code-language",
      "embedded-code",
    ],
    modifiers: ["strong", "emphasis", "strikethrough"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: ["embedded-code"],
    modifierRoles: {
      strong: ["text", "heading", "link", "entity", "code"],
      emphasis: ["text", "heading", "link", "entity", "code"],
      strikethrough: ["text", "heading", "link", "entity", "code"],
    },
  },
  modelUrl: () => new URL("../models/markdown.onnx", import.meta.url).href,
};
export default model;
