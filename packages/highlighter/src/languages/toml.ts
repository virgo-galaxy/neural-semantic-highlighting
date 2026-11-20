import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "toml",
  manifest: {
    id: "toml",
    documentKinds: [
      {
        id: "toml",
        extensions: [".toml"],
      },
    ],
  },
  sha256: "529bc6c6d6792d763dcd542748b56f007c3188ad395bad03b0133467fb317db0",
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
  modelUrl: () => new URL("../models/toml.onnx", import.meta.url).href,
};
export default model;
