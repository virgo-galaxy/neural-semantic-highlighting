import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "yaml",
  manifest: {
    id: "yaml",
    documentKinds: [
      {
        id: "yaml",
        extensions: [".yaml", ".yml"],
      },
    ],
  },
  sha256: "7c6b6b75a01342f4dbeb973db13dd4cc4291d9644f5224cc4eec456dcbd00791",
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
  modelUrl: () => new URL("../models/yaml.onnx", import.meta.url).href,
};
export default model;
