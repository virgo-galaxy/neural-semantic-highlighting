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
  sha256: "73236e36696fdf9b14d5bfe3bc7b4743a51b4b3b037d01a0961556e5aa4b1a4b",
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
