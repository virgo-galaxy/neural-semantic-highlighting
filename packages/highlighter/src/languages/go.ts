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
  sha256: "714398ae0df38766ced84a4dd0866585ad233a7474100906ecf4d6ff115ce8d1",
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
