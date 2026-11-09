import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "csharp",
  manifest: {
    id: "csharp",
    documentKinds: [
      {
        id: "csharp",
        extensions: [".cs"],
      },
    ],
  },
  sha256: "fdd087f40f06d26c4a9612bcebef7b5711cb48f29c9e111cbcac0ccb75e4cff1",
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
      "class",
      "interface",
      "enum",
      "enum-member",
      "constructor",
      "method",
      "parameter",
      "variable",
      "property",
      "decorator",
      "function",
    ],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/csharp.onnx", import.meta.url).href,
};
export default model;
