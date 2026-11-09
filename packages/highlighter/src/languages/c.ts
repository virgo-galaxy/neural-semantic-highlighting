import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "c",
  manifest: {
    id: "c",
    documentKinds: [
      {
        id: "c",
        extensions: [".c", ".h"],
      },
    ],
  },
  sha256: "07834638820dcb384d816104f547cb400a09234e7c795c94db7cbf299a7209bb",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "number",
      "operator",
      "punctuation",
      "type",
      "enum",
      "enum-member",
      "function",
      "parameter",
      "variable",
      "property",
      "label",
      "decorator",
    ],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/c.onnx", import.meta.url).href,
};
export default model;
