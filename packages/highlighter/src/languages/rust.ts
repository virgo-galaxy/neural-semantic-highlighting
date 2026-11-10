import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "rust",
  manifest: {
    id: "rust",
    documentKinds: [
      {
        id: "rust",
        extensions: [".rs"],
      },
    ],
  },
  sha256: "c2bae69bbf78449b5f53f1a45489d9295fa15d35005ed2b8bebee2a2678240cc",
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
      "trait",
      "enum",
      "enum-member",
      "function",
      "parameter",
      "variable",
      "property",
      "type-parameter",
      "decorator",
      "label",
      "constant",
    ],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/rust.onnx", import.meta.url).href,
};
export default model;
