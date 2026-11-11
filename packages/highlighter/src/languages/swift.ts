import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "swift",
  manifest: {
    id: "swift",
    documentKinds: [
      {
        id: "swift",
        extensions: [".swift"],
      },
    ],
  },
  sha256: "e5e8d28143b0a74858cab50810aaf2f3eea2be92fa66cfd8e8d4129fe4f3b606",
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
  modelUrl: () => new URL("../models/swift.onnx", import.meta.url).href,
};
export default model;
