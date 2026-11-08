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
  sha256: "ca36f5bcd4485bb1a78b81d0e4c08d27201a86ad6f5e797833d9fba2bc66dff8",
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
