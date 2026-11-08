import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "bash",
  manifest: {
    id: "bash",
    documentKinds: [
      {
        id: "bash",
        extensions: [".sh", ".bash", ".zsh", ".csh", ".tcsh"],
      },
    ],
  },
  sha256: "69e515b768fb399bda1d6716d3466838c8e858d1025d08992a49698a964d454e",
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
    ],
    modifiers: ["declaration", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: ["string"],
    modifierRoles: {
      declaration: ["function", "variable"],
      "default-library": ["function"],
    },
  },
  modelUrl: () => new URL("../models/bash.onnx", import.meta.url).href,
};
export default model;
