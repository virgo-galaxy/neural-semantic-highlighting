import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "python",
  manifest: {
    id: "python",
    documentKinds: [
      {
        id: "python",
        extensions: [".py", ".pyw", ".pyi"],
      },
    ],
  },
  sha256: "306c22ab5df354527293267abe6443489b0d249635fdaba05cd24bfe130905be",
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
      "function",
      "method",
      "parameter",
      "variable",
      "property",
      "decorator",
    ],
    modifiers: ["declaration", "async", "generator", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/python.onnx", import.meta.url).href,
};
export default model;
