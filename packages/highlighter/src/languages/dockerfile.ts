import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "dockerfile",
  manifest: {
    id: "dockerfile",
    documentKinds: [
      {
        id: "dockerfile",
        extensions: ["Dockerfile", ".dockerfile", "Containerfile", ".containerfile"],
      },
    ],
  },
  sha256: "951183564984ef37ccd1dbf5808762bd038171d238f9ce4806f8abb8258cbac1",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "number",
      "operator",
      "punctuation",
      "function",
      "variable",
      "parameter",
      "namespace",
      "property",
      "label",
    ],
    modifiers: ["declaration", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {
    modifierRoles: {
      declaration: ["variable", "property", "label", "function"],
      "default-library": ["function"],
    },
    coalesceAdjacentTokenTypes: ["string"],
  },
  modelUrl: () => new URL("../models/dockerfile.onnx", import.meta.url).href,
};
export default model;
