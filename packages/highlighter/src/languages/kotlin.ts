import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "kotlin",
  manifest: {
    id: "kotlin",
    documentKinds: [
      {
        id: "kotlin",
        extensions: [".kt", ".kts"],
      },
    ],
  },
  sha256: "c7987d7d6a2e411b31f173b4c9499ce4e379e7fc726c72549949178789f79fd6",
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
  modelUrl: () => new URL("../models/kotlin.onnx", import.meta.url).href,
};
export default model;
