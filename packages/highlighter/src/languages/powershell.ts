import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "powershell",
  manifest: {
    id: "powershell",
    documentKinds: [
      {
        id: "powershell",
        extensions: [".ps1", ".psm1", ".psd1"],
      },
    ],
  },
  sha256: "d0b3bdc10bd2c1feb446d104f4253c25183aed49261f9962e81cd5f314f38cba",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "number",
      "operator",
      "punctuation",
      "type",
      "function",
      "parameter",
      "variable",
      "property",
      "namespace",
    ],
    modifiers: ["declaration", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: ["comment"],
    modifierRoles: {
      declaration: ["function", "variable", "type"],
      "default-library": ["function", "variable"],
    },
  },
  modelUrl: () => new URL("../models/powershell.onnx", import.meta.url).href,
};
export default model;
