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
  sha256: "828ef4d0cf69a788a98f450dda80e867d65a2725b0fcc994f67804c5dfcba45a",
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
