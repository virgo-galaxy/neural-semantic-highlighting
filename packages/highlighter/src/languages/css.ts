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
  sha256: "a8289f9e82a09fb7e54cd96e8d572f380dd5b600eb84f0562513d2c8034525f3",
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
