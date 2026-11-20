import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "json",
  manifest: {
    id: "json",
    documentKinds: [
      {
        id: "json",
        extensions: [".json"],
      },
      {
        id: "jsonc",
        extensions: [".jsonc", ".code-workspace"],
      },
    ],
  },
  sha256: "8dbb80ef311ca76327e6e329f7ad2fb53e1a8ed3ea07783b1f5a458330bccdbf",
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
  modelUrl: () => new URL("../models/json.onnx", import.meta.url).href,
};
export default model;
