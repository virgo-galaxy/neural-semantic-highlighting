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
  sha256: "cbb5cf1492a925921e355350dbe0d2ce665228eedd7c4f0d2121a746ffab492e",
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
