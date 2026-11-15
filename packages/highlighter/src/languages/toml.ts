import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "toml",
  manifest: {
    id: "toml",
    documentKinds: [
      {
        id: "toml",
        extensions: [".toml"],
      },
    ],
  },
  sha256: "1a2aea71fe4a061552c3e1c9b4b81dc0dd32b6d8d526a5b4b57d58cf08ee81bc",
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
  modelUrl: () => new URL("../models/toml.onnx", import.meta.url).href,
};
export default model;
