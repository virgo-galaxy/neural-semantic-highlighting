import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "r",
  manifest: {
    id: "r",
    documentKinds: [
      {
        id: "r",
        extensions: [".R", ".r", ".Rprofile"],
      },
    ],
  },
  sha256: "3c02766d70c34f635b2262e41c46436fcce4cbc8661c5075df6decdbdae937ce",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "number",
      "operator",
      "punctuation",
      "namespace",
      "type",
      "enum",
      "enum-member",
      "function",
      "method",
      "constructor",
      "parameter",
      "variable",
      "property",
      "type-parameter",
      "decorator",
      "constant",
      "label",
    ],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/r.onnx", import.meta.url).href,
};
export default model;
