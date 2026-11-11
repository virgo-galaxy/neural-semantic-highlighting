import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "lua",
  manifest: {
    id: "lua",
    documentKinds: [
      {
        id: "lua",
        extensions: [".lua"],
      },
    ],
  },
  sha256: "a92fd40b9dc089b158d8867d95500f9d0bd9ac489ef9d262df0738f0a4ce1c4e",
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
  modelUrl: () => new URL("../models/lua.onnx", import.meta.url).href,
};
export default model;
