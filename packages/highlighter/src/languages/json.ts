import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "json",
  manifest: {
    id: "json",
    documentKinds: [
      {
        id: "json",
        extensions: [".json"],
      },
      {
        id: "jsonc",
        extensions: [".jsonc", ".code-workspace"],
      },
    ],
  },
  sha256: "e58bb54a022acfb5ebe52a9c6c0e8e62c390ca9c5ad27fea2b3090716735bbbe",
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
  modelUrl: () => new URL("../models/json.onnx", import.meta.url).href,
};
export default model;
