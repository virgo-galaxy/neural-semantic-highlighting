import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "zig",
  manifest: {
    id: "zig",
    documentKinds: [
      {
        id: "zig",
        extensions: [".zig"],
      },
    ],
  },
  sha256: "acdfb92204bd0fe725aa27391eeabb6358be38bf3f7d8d57e76120eb6e4bdd62",
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
      "parameter",
      "type-parameter",
      "variable",
      "property",
      "constant",
      "label",
    ],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/zig.onnx", import.meta.url).href,
};
export default model;
