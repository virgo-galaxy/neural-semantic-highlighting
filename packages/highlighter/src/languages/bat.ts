import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "bat",
  manifest: {
    id: "bat",
    documentKinds: [
      {
        id: "bat",
        extensions: [".bat", ".cmd"],
      },
    ],
  },
  sha256: "c5c527c4d6501035d8c32077279d1ba4e50f2840dea2bef794f03c3cb105fff3",
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
    coalesceAdjacentTokenTypes: ["comment", "string"],
    modifierRoles: {
      declaration: ["function", "variable"],
      "default-library": ["function"],
    },
  },
  modelUrl: () => new URL("../models/bat.onnx", import.meta.url).href,
};
export default model;
