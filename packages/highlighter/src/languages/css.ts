import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "css",
  manifest: {
    id: "css",
    documentKinds: [
      {
        id: "css",
        extensions: [".css"],
      },
      {
        id: "scss",
        extensions: [".scss"],
      },
      {
        id: "less",
        extensions: [".less"],
      },
    ],
  },
  sha256: "65f244b0447b3d2251bfecad9ba8bcf092a9aa45c01f1f3e4ff47031c61f94bc",
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
      "class",
      "function",
      "parameter",
      "variable",
      "property",
      "label",
      "tag",
      "attribute",
    ],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/css.onnx", import.meta.url).href,
};
export default model;
