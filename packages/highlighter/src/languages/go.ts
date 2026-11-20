import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "go",
  manifest: {
    id: "go",
    documentKinds: [
      {
        id: "go",
        extensions: [".go"],
      },
    ],
  },
  sha256: "d61b4838333ad5109201b833786292542691ae4210b0e24c86d7f90d3fabf827",
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
      "interface",
      "type-parameter",
      "function",
      "method",
      "parameter",
      "variable",
      "property",
      "label",
    ],
    modifiers: ["declaration", "readonly", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/go.onnx", import.meta.url).href,
};
export default model;
