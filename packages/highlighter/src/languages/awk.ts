import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "awk",
  manifest: {
    id: "awk",
    documentKinds: [
      {
        id: "awk",
        extensions: [".awk", ".gawk"],
      },
    ],
  },
  sha256: "5bacf9a4b573e139460e3f6aa9fd114f7bdaaac2645d464aa7b5342832b6a8f7",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "number",
      "regexp",
      "operator",
      "punctuation",
      "function",
      "variable",
    ],
    modifiers: ["declaration", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {
    modifierRoles: {
      declaration: ["function", "variable"],
      "default-library": ["function", "variable"],
    },
  },
  modelUrl: () => new URL("../models/awk.onnx", import.meta.url).href,
};
export default model;
