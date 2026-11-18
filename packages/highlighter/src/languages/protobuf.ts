import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "protobuf",
  manifest: {
    id: "protobuf",
    documentKinds: [
      {
        id: "protobuf",
        extensions: [".proto"],
      },
    ],
  },
  sha256: "f5aebafb3faf5e00655c833028a51363332d3a75e6a377f0b27a8f1470fbe92e",
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
      "namespace",
      "property",
      "method",
      "label",
      "constant",
    ],
    modifiers: ["declaration", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: ["string", "comment"],
    modifierRoles: {
      declaration: ["type", "enum", "enum-member", "property", "namespace", "method", "label"],
      "default-library": ["type"],
    },
  },
  modelUrl: () => new URL("../models/protobuf.onnx", import.meta.url).href,
};
export default model;
