import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "dart",
  manifest: {
    id: "dart",
    documentKinds: [
      {
        id: "dart",
        extensions: [".dart"],
      },
    ],
  },
  sha256: "a91121120cccbde17d5e0c59865523ea3b2eaee269a3016ac8ab8a40845efc5d",
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
  modelUrl: () => new URL("../models/dart.onnx", import.meta.url).href,
};
export default model;
