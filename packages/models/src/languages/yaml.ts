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
  sha256: "3a20c5ec6e9f46b752715f69aa04860336bf63a5bc9b1f66656646a797db68ed",
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
  modelUrl: () =>
    new URL(
      "../assets/v1/yaml/3a20c5ec6e9f46b752715f69aa04860336bf63a5bc9b1f66656646a797db68ed.onnx",
      import.meta.url,
    ).href,
};
export default model;
