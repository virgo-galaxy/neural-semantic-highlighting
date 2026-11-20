import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "dart",
  manifest: {
    id: "dart",
    documentKinds: [
      {
        id: "dart",
        extensions: [".dart"],
      },
    ],
  },
  sha256: "64b79f1fe5941e4f505e8936161067c5bc5af2ceb16083502b4499f03a0bbdc8",
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
  inferenceWindowing: {
    format: "nsh-overlap-logits-v1",
    strideBytes: 128,
    edgeWeightCap: 128,
    adaptiveWeight: 0,
  },
  modelUrl: () => new URL("../models/dart.onnx", import.meta.url).href,
};
export default model;
