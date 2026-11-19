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
  sha256: "c49fa9d6a1bf01004921521b9138c2b9fe9657b8874760027f9376c44afe2f7b",
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
  inferenceWindowing: {
    format: "nsh-overlap-logits-v1",
    strideBytes: 128,
    edgeWeightCap: 128,
    adaptiveWeight: 0,
  },
  modelUrl: () => new URL("../models/zig.onnx", import.meta.url).href,
};
export default model;
