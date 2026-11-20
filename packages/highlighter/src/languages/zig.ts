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
  sha256: "fc188499ced1a08faa3bf3d900b7eebe1403d52ae5a718f21f0f31491071e377",
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
